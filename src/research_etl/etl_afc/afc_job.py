import os
import re
import datetime
import tarfile
import shutil
import tempfile
from typing import List
from typing import Optional

import sqlalchemy as sa

from research_etl.utils.util_rds import DatabaseManager
from research_etl.utils.util_rds import afc_copy
from research_etl.utils.util_logging import ProcessLogger
from research_etl.etl_afc.lookup_tables import deviceclass
from research_etl.etl_afc.lookup_tables import event
from research_etl.etl_afc.lookup_tables import eventgroup
from research_etl.etl_afc.lookup_tables import holiday
from research_etl.etl_afc.lookup_tables import mbta_weekend_service
from research_etl.etl_afc.lookup_tables import routes
from research_etl.etl_afc.lookup_tables import tariffversions
from research_etl.etl_afc.lookup_tables import tickettype
from research_etl.etl_afc.lookup_tables import tvmstation
from research_etl.etl_afc.lookup_tables import tvmtable
from research_etl.etl_afc.lookup_tables import LookupTables
from research_etl.utils.util_aws import file_list_from_s3
from research_etl.utils.util_aws import rename_s3_object
from research_etl.utils.util_aws import delete_object
from research_etl.utils.util_aws import download_file


def verify_partition(date: datetime.date, table: str, db_manager: DatabaseManager) -> None:
    """
    check if table partition exists for afc table and date
    if does not exist, create partition
    """
    partition_table = f"{table}_y{date.strftime('%Y')}m{date.strftime('%m')}"
    check_query = (
        "SELECT EXISTS ( "
        "    SELECT FROM pg_tables WHERE "
        "       schemaname = 'afc' "
        f"       AND tablename = '{partition_table}'"
        ");"
    )
    check_bool = db_manager.select_as_list(sa.text(check_query))[0]["exists"]

    if check_bool:
        # table already exists, do nothing
        return

    # create new partition table
    from_month = datetime.date(date.year, date.month, 1)
    if date.month == 12:
        to_month = datetime.date(date.year + 1, 1, 1)
    else:
        to_month = datetime.date(date.year, date.month + 1, 1)

    create_query = (
        f"CREATE TABLE afc.{partition_table} PARTITION OF afc.{table} "
        f"FOR VALUES FROM ('{from_month}') TO ('{to_month}');"
    )
    db_manager.execute(sa.text(create_query))


def get_afc_headers(afc_type: str) -> Optional[List[str]]:
    """
    return columns headers for specified afc type
    """
    afc_headers = {
        "faregate": [
            "trxtime",
            "servicedate",
            "deviceclassid",
            "deviceid",
            "uniquemsid",
            "eventsequno",
            "tariffversion",
            "tarifflocationid",
            "unplanned",
            "eventcode",
            "inserted",
        ],
        "ridership": [
            "deviceclassid",
            "deviceid",
            "uniquemsid",
            "salestransactionno",
            "sequenceno",
            "trxtime",
            "servicedate",
            "branchlineid",
            "fareoptamount",
            "tariffversion",
            "articleno",
            "card",
            "ticketstocktype",
            "tvmtarifflocationid",
            "movementtype",
            "bookcanc",
            "correctioncounter",
            "correctionflag",
            "tempbooking",
            "testsaleflag",
            "inserted",
        ],
    }

    return afc_headers.get(afc_type)


def load_afc_data(s3_object: str, db_manager: DatabaseManager, afc_type: str) -> None:
    """
    load fargate or ridership data into RDS from csv.gz file
    """
    headers = get_afc_headers(afc_type)
    if headers is None:
        raise IndexError(f"{afc_type} is not a supported AFC data load type")

    file_name = s3_object.split("/")[-1]

    # handle bulk import that could cover many monthly table partitions
    if "bulk_import" in file_name:
        start_date, end_date = re.findall(r"(\d{8})", file_name)[:2]

        start_date_dt = datetime.datetime.strptime(start_date, "%Y%m%d").date()
        end_date_dt = datetime.datetime.strptime(end_date, "%Y%m%d").date()

        partition_date = start_date_dt.replace(day=1)

        while partition_date <= end_date_dt:
            verify_partition(partition_date, afc_type, db_manager)
            if partition_date.month == 12:
                partition_date = partition_date.replace(year=partition_date.year + 1, month=1)
            else:
                partition_date = partition_date.replace(month=partition_date.month + 1)

        delete_query = (
            f"DELETE FROM afc.{afc_type} WHERE servicedate >= '{start_date_dt}' AND servicedate <= '{end_date_dt}';"
        )
        db_manager.execute(sa.text(delete_query))

    # handle import for one service_date
    else:
        service_date = datetime.datetime.strptime(file_name[:8], "%Y%m%d").date()

        verify_partition(service_date, afc_type, db_manager)

        delete_query = f"DELETE FROM afc.{afc_type} WHERE servicedate = '{service_date}';"
        db_manager.execute(sa.text(delete_query))

    afc_copy(s3_object, f"afc.{afc_type}", headers, null_as=False)


def load_lookups(s3_object: str, db_manager: DatabaseManager) -> None:
    """
    load afc_lookups_.csv.tar.gz file into RDS
    """
    # download lookup file to temp directory
    temp_dir = tempfile.mkdtemp()
    object_name = s3_object.split("/")[-1]
    full_local_path = os.path.join(temp_dir, object_name)
    download_file(s3_object, full_local_path)

    # extract csv files from tar archive
    afc_folder = os.path.join(temp_dir, "afc_lookups/")
    with tarfile.open(full_local_path) as afc_tar:
        afc_tar.extractall(afc_folder)

    afc_tables: List[LookupTables] = [
        deviceclass,
        event,
        eventgroup,
        holiday,
        mbta_weekend_service,
        routes,
        tariffversions,
        tickettype,
        tvmstation,
        tvmtable,
    ]

    for table in afc_tables:
        full_path = os.path.join(afc_folder, table["file_name"])
        table_name = f"afc.{table['file_name'].lower().replace('.csv','')}"
        db_manager.truncate_table(table_name, restart_identity=True)
        afc_copy(full_path, table_name, table["columns"])

    shutil.rmtree(temp_dir, ignore_errors=True)


def run(db_manager: DatabaseManager) -> None:
    """
    main job event loop

    list s3 objects from afc/in bucket and process any found files

    each found file should temporarily downloaded locally for processing and
    then deleted
    """
    s3_in_path = "afc_oracle_db/"
    s3_error_path = "afc_oracle_db_error/"
    s3_in_bucket = os.getenv("AFC_IN_BUCKET", "")

    process_log = ProcessLogger("afc_etl_job")

    for s3_object in sorted(file_list_from_s3(s3_in_bucket, s3_in_path)):
        object_name = s3_object.split("/")[-1]

        afc_log = ProcessLogger("afc_load_file", s3_object=s3_object)

        try:
            if "_ridership_" in object_name.lower():
                load_afc_data(s3_object, db_manager, "ridership")
            elif "_faregate_" in object_name.lower():
                load_afc_data(s3_object, db_manager, "faregate")
            elif "afc_lookups_" in object_name.lower():
                load_lookups(s3_object, db_manager)
            else:
                raise NotImplementedError(f"No AFC load process for: {s3_object}")

        except Exception as exception:
            rename_s3_object(s3_object, os.path.join(s3_in_bucket, s3_error_path, object_name))
            afc_log.log_failure(exception)
        else:
            delete_object(s3_object)
            afc_log.log_complete()

    process_log.log_complete()


if __name__ == "__main__":
    local_db = DatabaseManager()
    run(local_db)
