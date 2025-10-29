import os
import datetime
import tempfile

from pyarrow import csv
import pyarrow as pa
import pyarrow.dataset as pd
import pyarrow.compute as pc

from research_etl.utils.util_rds import DatabaseManager
from research_etl.utils.util_rds import copy_gzip_csv_to_db
from research_etl.utils.util_aws import assume_role_session
from research_etl.utils.util_logging import ProcessLogger
from research_etl.etl_sb_api import sb_tables
from research_etl.utils.parquet import ds_from_path
from research_etl.utils.parquet import ds_metadata_min_max
from research_etl.utils.parquet import ds_group_jobids


SB_SCHEMA = "sb_api"
BUCKET = os.getenv("SPRINGBOARD_BUCKET", "")
SB_PREFIX = os.path.join(BUCKET, "odin", "data", "sb", "api", "")

# The schema for these tables is defined in "tests/init_schema.sql"
# These tables are automatically created on a new build of the DEV docker postgres instance
#
# These tables must be manually created in the AWS Research Server DB. This database has no
# automated migration tooling. TID Infra Team has 'postgres' credentials that can be used to perform
# these manual steps.
SB_TABLES = [
    sb_tables.person,
    sb_tables.tvmtable,
    sb_tables.media,
    sb_tables.trips,
    sb_tables.mainshift,
    sb_tables.sales_txns,
    sb_tables.validation_taps,
    sb_tables.shiftevent,
    sb_tables.cashless_payments,
    sb_tables.inspections,
]


def create_partitions(ds: pd.dataset, table: sb_tables.SBTable, db: DatabaseManager) -> None:
    """
    Create DB partition tables based on range of dates from parquet dataset.

    :param ds: parquet dataset
    :param table: DB table details
    :param db: DB Manager for partition table creation
    """
    # Pull min/max of `part_column` partition column from parquet dataset.
    # This will be used for determining which partition tables may need to be created
    d_min: datetime.datetime
    d_max: datetime.datetime
    d_min, d_max = ds_metadata_min_max(ds, table.part_column)
    from_dt = datetime.datetime(year=d_min.year, month=d_min.month, day=1)
    end_dt = datetime.datetime(year=d_max.year, month=d_max.month, day=1)

    # partition tables appear as individual tables in the postgres schema, but when created are
    # "attached" to the primary table with partitioning rules.
    # this query finds all partition tables associated with the primary "table_name" of `table`
    # this list of partition tables is used to check if any new partition tables need to be created
    tables_query = (
        f"SELECT tablename FROM pg_tables WHERE schemaname = '{SB_SCHEMA}'"
        f" AND starts_with(tablename, '{table.table_name}_y');"
    )
    db_tables: list[str] = [d.get("tablename") for d in db.select_as_list(tables_query)]

    while from_dt <= end_dt:
        # create partition table name as:
        #   - table_name_y(YYYY)_m(mm)
        partition_table = f"{table.table_name}_y{from_dt.strftime('%Y')}m{from_dt.strftime('%m')}"
        # set to_dt +1 month of from_dt on every iteration
        if from_dt.month == 12:
            to_dt = datetime.datetime(from_dt.year + 1, 1, 1)
        else:
            to_dt = datetime.datetime(from_dt.year, from_dt.month + 1, 1)
        create_query = (
            f"CREATE TABLE {SB_SCHEMA}.{partition_table} PARTITION OF {SB_SCHEMA}.{table.table_name} "
            f"FOR VALUES FROM ('{from_dt}') TO ('{to_dt}');"
        )
        if partition_table not in db_tables:
            # if partition_table not already created, execute CREATE TABLE ** PARTITION OF **
            # statement. FROM values is inclusive of provided value TO value is exclusive
            db.execute(create_query)
        from_dt = to_dt


def load_table_to_db(data: pa.Table, db_table: str) -> None:
    """
    Load pyarrow Table into database.

    This function takes a materialized pyarrow Table (that should fit in memory), write it to a CSV
    file and then loads the CSV into the database with a COPY command.

    :param data:
    :param db_table: name of DB table to load `data` into
    """
    with tempfile.TemporaryDirectory() as t_dir:
        init_csv_path = os.path.join(t_dir, "out.csv")
        write_options = csv.WriteOptions(include_header=True)
        csv.write_csv(data, init_csv_path, write_options=write_options)
        # the pyarrow csv.write_csv function with `include_header=True` writes duplicate
        # header rows to the csv file. I think this is related to the input Table spanning
        # multiple row groups in the source parquet dataset.
        # so we re-write the csv file, removing any duplicated header rows, if found
        final_csv_path = os.path.join(t_dir, "final.csv")
        with open(init_csv_path, "r", encoding="utf8") as r_file, open(final_csv_path, "w", encoding="utf8") as o_file:
            first_line = r_file.readline()
            o_file.write(first_line)
            for line in r_file:
                if line == first_line:
                    continue
                o_file.write(line)
        copy_gzip_csv_to_db(final_csv_path, db_table)


# pylint: disable=too-many-locals
def sb_api_load_job(db_manager: DatabaseManager, table: sb_tables.SBTable) -> None:
    """
    S&B API data loading job.

    This is the business logic for loading S&B API table data from a parquet dataset to a
    postgres DB table. It assumes an AWS role that has access to the S3 bucket
    containing the parquet dataset and KMS decryption permissions.

    :param db_manager: DB Manager for database calls
    :param table: DB table details
    """
    # Assume aws role within tid-main for S3 access / KMS decryption
    session = assume_role_session(os.getenv("ROLE_ARN_WITHIN_TID_FOR_KMS_ACCESS", ""))

    ds_path = os.path.join("s3://", SB_PREFIX, table.table_name, "")
    ds = ds_from_path(ds_path, session=session)
    if ds.count_rows() == 0:
        # no data in parquet dataset
        return

    schema_table = f"{SB_SCHEMA}.{table.table_name}"
    max_job_id_query = f"SELECT MAX(job_id) FROM {schema_table};"
    max_db_job_id: int = db_manager.select_as_list(max_job_id_query)[0]["max"]
    max_pq_job_id: int
    _, max_pq_job_id = ds_metadata_min_max(ds, "job_id")
    if max_db_job_id == max_pq_job_id:
        # no new records in parquet dataset
        return

    if table.table_type == "static":
        static_log = ProcessLogger("sb_api_static_load", table=table.table_name)
        db_manager.truncate_table(schema_table)
        load_table_to_db(ds.to_table(), schema_table)
        static_log.log_complete()
    else:
        # transaction type table
        part_log = ProcessLogger(
            "sb_api_transaction_load",
            table=table.table_name,
        )
        create_partitions(ds, table, db_manager)
        # load records for transaction table in batches
        # target batch size that will create CSV files ~256MB in size.
        # estimate assumes 8 bytes per column
        target_rows = int(256 * 1024 * 1024 / (8 * len(ds.schema)))
        load_job_id_start = 0
        load_job_id_end = 0
        load_rows = 0
        for api_job in ds_group_jobids(ds, min_job_id=max_db_job_id):
            load_rows += api_job["count"]
            if load_job_id_start == 0:
                load_job_id_start = api_job["job_id"]
            load_job_id_end = api_job["job_id"]

            if load_rows > target_rows:
                load_filter = (pc.field("job_id") >= load_job_id_start) & (pc.field("job_id") <= load_job_id_end)
                part_log.add_metadata(
                    table_rows=load_rows,
                    job_id_from=load_job_id_start,
                    job_id_to=load_job_id_end,
                    print_log=True,
                )
                load_table_to_db(ds.to_table(filter=load_filter), schema_table)
                load_job_id_start = 0
                load_rows = 0

        if load_rows > 0:
            load_filter = (pc.field("job_id") >= load_job_id_start) & (pc.field("job_id") <= load_job_id_end)
            part_log.add_metadata(
                table_rows=load_rows,
                job_id_from=load_job_id_start,
                job_id_to=load_job_id_end,
                print_log=True,
            )
            load_table_to_db(ds.to_table(filter=load_filter), schema_table)

        part_log.log_complete()


# pylint: enable=too-many-locals


def run(db_manager: DatabaseManager) -> None:
    """
    event loop for S&B API loading job
    """
    for table in SB_TABLES:
        try:
            log = ProcessLogger("sb_api_load_job", table=table.table_name)
            sb_api_load_job(db_manager, table)
            log.log_complete()
        except Exception as exception:
            log.log_failure(exception)
