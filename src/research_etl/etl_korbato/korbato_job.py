import os
import tempfile
import datetime
from io import StringIO

import paramiko
import sqlalchemy as sa

from research_etl.utils.util_logging import ProcessLogger
from research_etl.utils.util_rds import DatabaseManager
from research_etl.utils.util_rds import copy_zip_csv_to_db
from research_etl.utils.util_sftp import walk_sftp_dirs


def verify_partition(date: datetime.date, table: str, db_manager: DatabaseManager) -> None:
    """
    check if table partition exists for odx2 table and date
    if does not exist, create partition
    """
    partition_table = f"{table}_y{date.strftime('%Y')}m{date.strftime('%m')}"
    check_query = (
        "SELECT EXISTS ( "
        "    SELECT FROM pg_tables WHERE "
        "       schemaname = 'odx2' "
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
        f"CREATE TABLE odx2.{partition_table} PARTITION OF odx2.{table} "
        f"FOR VALUES FROM ('{from_month}') TO ('{to_month}');"
    )
    db_manager.execute(sa.text(create_query))


def connect_ssh_client(hostname: str = "", username: str = "") -> paramiko.SSHClient:
    """
    get/create paramiko sftp client
    """
    logger = ProcessLogger("create_ssh_client")
    logger.log_start()

    if hostname == "":
        hostname = os.getenv("KORBATO_HOSTNAME", "")
    if username == "":
        username = os.getenv("KORBATO_USERNAME", "")

    env_ssh_key = os.getenv("KORBATO_SSHKEY", "")

    ssh_key = paramiko.Ed25519Key.from_private_key(StringIO(env_ssh_key))

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=hostname,
            username=username,
            pkey=ssh_key,
        )
    except Exception as exception:
        logger.log_failure(exception)
        raise exception

    logger.log_complete()

    return client


def download_sftp_file(sftp_path: str, local_path: str, sftp_client: paramiko.SFTPClient) -> None:
    """
    download an sftp_path to a local_path
    """
    download_logger = ProcessLogger("sftp_download", sftp_path=sftp_path, local_path=local_path)
    download_logger.log_start()

    try:
        sftp_client.get(sftp_path, local_path)

    except Exception as exception:
        download_logger.log_failure(exception)
        raise exception

    download_logger.log_complete()


def load_korbato_file(local_path: str, db_manager: DatabaseManager) -> None:
    """
    load one korbato file into rds

    /tmp/20240309_vehicle_day_20240312-200001.csv.zip_u569z9u
    """
    file_name = local_path.split("/")[-1]

    schema = os.getenv("KORBATO_SCHEMA", "")

    # handle data tables
    if file_name[:8].isnumeric():
        year = int(file_name[:4])
        month = int(file_name[4:6])
        day = int(file_name[6:8])
        service_date = datetime.date(year, month, day)

        table = file_name[9:].rsplit("_", 1)[0]

        if table == "fare_transaction":
            verify_partition(service_date, table, db_manager)

        del_q = sa.text(f"DELETE FROM {schema}.{table} WHERE svc_date = '{year}-{month}-{day}'")
        db_manager.execute(del_q)

    # handle lookup tables
    else:
        table = file_name.rsplit("_", 1)[0]
        db_manager.truncate_table(f"{schema}.{table}")

    copy_zip_csv_to_db(local_path, f"{schema}.{table}")


def run(db_manager: DatabaseManager) -> None:
    """
    main job event loop

    load any csv.zip files available in the Korbato SFTP folder
    """
    process_logger = ProcessLogger("etl_korbato")
    process_logger.log_start()

    try:
        ssh_client = connect_ssh_client()
        sftp_client = ssh_client.open_sftp()

        sftp_paths = walk_sftp_dirs(sftp_client, "out")

        process_logger.add_metadata(file_count=len(sftp_paths))
        for sftp_path in sftp_paths:
            sftp_file = sftp_path.split("/")[-1]
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
                temp_file = os.path.join(temp_dir, sftp_file)
                download_sftp_file(sftp_path, temp_file, sftp_client)
                load_korbato_file(temp_file, db_manager)

        sftp_client.close()
        ssh_client.close()

        process_logger.log_complete()

    except Exception as exception:
        process_logger.log_failure(exception)


def alt_run(db_manager: DatabaseManager) -> None:
    """
    main job event loop

    load any csv.zip files available in the catch-up Korbato SFTP folder
    """
    process_logger = ProcessLogger("catch_up_korbato")
    process_logger.log_start()

    try:
        ssh_client = connect_ssh_client(
            hostname="sftp.korbato.com",
        )
        sftp_client = ssh_client.open_sftp()

        sftp_paths = walk_sftp_dirs(sftp_client, "out/202408")

        process_logger.add_metadata(file_count=len(sftp_paths))
        for sftp_path in sftp_paths:
            sftp_file = sftp_path.split("/")[-1]
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
                temp_file = os.path.join(temp_dir, sftp_file)
                download_sftp_file(sftp_path, temp_file, sftp_client)
                load_korbato_file(temp_file, db_manager)

        sftp_client.close()
        ssh_client.close()

        process_logger.log_complete()

    except Exception as exception:
        process_logger.log_failure(exception)


if __name__ == "__main__":
    local_db = DatabaseManager()
    run(local_db)
