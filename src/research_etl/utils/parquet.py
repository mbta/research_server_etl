import os
import re
from typing import Tuple
from typing import Sequence
from typing import Union
from typing import Any
from typing import TypedDict
from operator import itemgetter
import boto3

import pyarrow.parquet as pq
import pyarrow.dataset as pd
import pyarrow.compute as pc
import pyarrow.acero as ac
from pyarrow import fs

from research_etl.utils.util_logging import ProcessLogger
from research_etl.utils.util_aws import list_objects
from research_etl.utils.util_aws import get_s3_client


class RowGroupStats(TypedDict):
    """Incomplete representation of Stats fields, but only ones currently used."""

    has_min_max: bool
    max: Any
    min: Any
    null_count: int
    num_values: int


def file_column_stats(pq_meta: pq.FileMetaData, column: str) -> list[RowGroupStats]:
    """
    Retrieve 'column' statistics from metadata of parquet file.

    :param pq_meta: Metadata of parquet file.
    :param column: Name of column to retrieve stats for.

    :return: List of RowGroupStats, each List index correspends File RowGroup of same index.
    """
    col_index = pq_meta.schema.to_arrow_schema().get_field_index(column)
    assert col_index >= 0
    file_stats = []
    for rg_index in range(pq_meta.num_row_groups):
        rg_stats: RowGroupStats = pq_meta.row_group(rg_index).column(col_index).to_dict()["statistics"]
        file_stats.append(rg_stats)

    return file_stats


def ds_from_path(source: Union[str, Sequence[str]], session: boto3.Session = None) -> pd.UnionDataset:
    """
    Create pyarrow Dataset from parquet path(s). If multiple paths, schemas must be unionable.

    :param source: parquet file path(s) on local disk or S3, if S3 must start with s3://
    :param session: Optional boto3.Session to use for S3 access (e.g. from assumed role)
    :return: pyarrow Dataset of path(s) with "unionable" schema

    Example usage:
        from research_etl.utils.util_aws import assume_role_session
        from research_etl.utils.parquet import ds_from_path
        session = assume_role_session("arn:aws:iam::123456789012:role/YourRole")
        ds = ds_from_path("s3://bucket/prefix", session=session)
    """
    log = ProcessLogger("ds_from_path")
    paths = []
    if isinstance(source, str):
        # single parquet file
        if source.endswith(".parquet"):
            paths.append(source)
        # S3 partition path
        elif source.startswith("s3://"):
            s3_client = get_s3_client(session=session) if session is not None else None
            paths = [o.path for o in list_objects(source, in_filter=".parquet", s3_client=s3_client)]
        # local partition path
        else:
            for w_dir, _, files in os.walk(source):
                paths += [os.path.join(w_dir, f) for f in files if f.endswith(".parquet")]
    elif isinstance(source, Sequence):
        paths = [f for f in source if f.endswith(".parquet")]
    log.add_metadata(num_source=len(paths), paths=",".join(paths))

    if isinstance(source, str) and source.startswith("s3://"):  # temporary workaround for pyarrow s3 permissions issue
        log.add_metadata(status="Using temporary workaround for pyarrow s3 permissions issue")
        sts_client = boto3.client("sts")
        assumed_role = sts_client.assume_role(
            RoleArn=os.getenv("ROLE_ARN_WITHIN_TID_FOR_KMS_ACCESS", ""),
            RoleSessionName="session_name",
            DurationSeconds=43200,
        )
        credentials = assumed_role["Credentials"]

        s3 = fs.S3FileSystem(
            access_key=credentials["AccessKeyId"],
            secret_key=credentials["SecretAccessKey"],
            session_token=credentials["SessionToken"],
            region="us-east-1",
        )

        # remove s3:// prefix (pyarrow doesn't accept it if filesystem is explicitly provided)
        paths = [path[5:] if path.startswith("s3://") else path for path in paths]

        ds = pd.dataset([pd.dataset(part, partitioning="hive", format="parquet", filesystem=s3) for part in paths])
    else:
        ds = pd.dataset([pd.dataset(part, partitioning="hive", format="parquet") for part in paths])

    log.log_complete(num_sources=len(paths))
    return ds


def ds_metadata_min_max(ds: pd.UnionDataset, column: str) -> Tuple[Any, Any]:
    """
    Get min & max value of column from Dataset metadata.

    This is a very fast and efficient way to get min/max from large dataset with accurate
    metadata statistics.

    If the `column` contains all NULL values, return values will be `None`.

    If the `column` is a path partition, return values will be type str.

    :param ds: pyarrow.Dataset to scan
    :param column: column to query

    :return: (min, max)
    """
    log = ProcessLogger("ds_metadata_min_max", column=column)
    column_mins = []
    column_maxs = []
    try:
        for child in ds.children:
            # check if column in ds partition
            joined_files = ",".join(child.files)
            if f"/{column}=" in joined_files:
                column_re = re.compile(rf"\/{column}=([^\/]*)\/")
                column_parts = column_re.findall(joined_files)
                column_mins += column_parts
                column_maxs += column_parts
                continue
            for frag in child.get_fragments():
                metadata: pq.FileMetaData = frag.metadata
                if column in ds.schema.names and column not in metadata.schema.names:
                    # column in dataset but not fragment file
                    continue
                for col_stats in file_column_stats(metadata, column):
                    if col_stats["min"] is not None:
                        column_mins.append(col_stats["min"])
                    if col_stats["max"] is not None:
                        column_maxs.append(col_stats["max"])
        col_min = None
        if column_mins:
            col_min = min(column_mins)
        col_max = None
        if column_maxs:
            col_max = max(column_maxs)
        log.log_complete()
    except Exception as exception:
        log.log_failure(exception)
        raise exception

    return (col_min, col_max)


class JobGroups(TypedDict):
    """Retrun structure of ds_group_jobids"""

    job_id: int
    count: int


def ds_group_jobids(ds: pd.Dataset, min_job_id: int | None = None) -> list[JobGroups]:
    """
    Perform group-by operation of job_ids, resulting in number of records per job_id.

    :param ds: pyarrow.Dataset to scan
    :param min_job_id: Only group job_id's greater than this (exclusive)

    :return: sorted list of job_id's with a record count (per job_id) ascending
    """
    columns = ["job_id"]
    log = ProcessLogger("ds_group_jobids", min_job_id=min_job_id)
    scan_node = ac.ScanNodeOptions(ds, columns=columns, batch_readahead=16, fragment_readahead=1)
    declarations = [ac.Declaration("scan", scan_node)]
    if min_job_id is not None:
        declarations.append(ac.Declaration("filter", ac.FilterNodeOptions(pc.field("job_id") > min_job_id)))
    declarations.append(
        ac.Declaration(
            "aggregate", ac.AggregateNodeOptions(aggregates=[(columns, "hash_count", None, "count")], keys=columns)
        ),
    )
    table = ac.Declaration.from_sequence(declarations).to_table().to_pylist()
    table = sorted(table, key=itemgetter("job_id"))
    log.log_complete(num_job_ids=len(table))
    return table
