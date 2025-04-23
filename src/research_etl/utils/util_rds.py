import os
import csv
import gzip
import time
import zipfile
import platform
import subprocess
import urllib.parse as urlparse
from typing import Any, Dict, List, Tuple, Union

import boto3
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from research_etl.utils.util_logging import ProcessLogger


def running_in_docker() -> bool:
    """
    return True if running inside of a docker container, else False
    """
    path = "/proc/self/cgroup"
    return (
        os.path.exists("/.dockerenv")
        or os.path.isfile(path)
        and any("docker" in line for line in open(path, encoding="UTF-8"))
    )


def running_in_aws() -> bool:
    """
    return True if running on aws, else False
    """
    return bool(os.getenv("AWS_DEFAULT_REGION"))


def get_db_host() -> str:
    """
    get current db_host string
    """
    db_host = os.environ.get("DB_HOST", "")

    # on mac, when running in docker locally db is accessed by "0.0.0.0" ip
    if db_host == "dmap_local_rds" and "macos" in platform.platform().lower():
        db_host = "0.0.0.0"

    # when running application locally in CLI for configuration
    # and debugging, db is accessed by localhost ip
    if not running_in_docker() and not running_in_aws():
        db_host = "127.0.0.1"

    return db_host


def get_db_password() -> str:
    """
    function to provide rds password

    used to refresh auth token, if required
    """
    db_password = os.environ.get("DB_PASSWORD", None)
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_user = os.environ.get("DB_USER")
    db_region = os.environ.get("DB_REGION", None)

    if db_password is None:
        # generate aws db auth token if in rds
        client = boto3.client("rds")
        return client.generate_db_auth_token(
            DBHostname=db_host,
            Port=db_port,
            DBUsername=db_user,
            Region=db_region,
        )

    return db_password


def create_db_connection_string() -> str:
    """
    produce database connection string from environment
    """
    process_log = ProcessLogger("create_db_connection_string")

    db_host = get_db_host()
    db_name = os.environ.get("DB_NAME")
    db_password = os.environ.get("DB_PASSWORD", None)
    db_port = os.environ.get("DB_PORT")
    db_user = os.environ.get("DB_USER")
    db_ssl_options = ""

    assert db_host is not None
    assert db_name is not None
    assert db_port is not None
    assert db_user is not None

    process_log.add_metadata(host=db_host, database_name=db_name, user=db_user, port=db_port)

    # use presence of DB_PASSWORD env var as indicator of connection type.
    #
    # if not available, assume cloud database where ssl is used and
    # passwords are generated on the fly
    #
    # if is available, assume local dev usage
    if db_password is None:
        db_password = get_db_password()
        db_password = urlparse.quote_plus(db_password)

        assert db_password is not None
        assert db_password != ""

        # set the ssl cert path to the file that should be added to the
        # lambda function at deploy time
        db_ssl_cert = os.path.abspath(os.path.join("/", "usr", "local", "share", "amazon-certs.pem"))

        assert os.path.isfile(db_ssl_cert)

        # update the ssl options string to add to the database url
        db_ssl_options = f"?sslmode=verify-full&sslrootcert={db_ssl_cert}"

    process_log.log_complete()

    return f"{db_user}:{db_password}@{db_host}:{db_port}/{db_name}{db_ssl_options}"


def postgres_event_update_db_password(
    _: sa.engine.interfaces.Dialect,
    __: Any,
    ___: Tuple[Any, ...],
    cparams: Dict[str, Any],
) -> None:
    """
    update database passord on every new connection attempt
    this will refresh db auth token passwords
    """
    process_logger = ProcessLogger("password_refresh")
    cparams["password"] = get_db_password()
    process_logger.log_complete()


def get_local_engine(
    echo: bool = False,
) -> sa.future.engine.Engine:
    """
    Get an SQL Alchemy engine that connects to a locally Postgres RDS stood up
    via docker using env variables
    """
    process_logger = ProcessLogger("create_sql_engine")
    try:
        database_url = f"postgresql+psycopg2://{create_db_connection_string()}"

        engine = sa.create_engine(
            database_url,
            echo=echo,
            future=True,
            pool_pre_ping=True,
            pool_use_lifo=True,
            pool_size=3,
            max_overflow=2,
            connect_args={
                "keepalives": 1,
                "keepalives_idle": 60,
                "keepalives_interval": 60,
            },
        )

        process_logger.log_complete()
        return engine
    except Exception as exception:
        process_logger.log_failure(exception)
        raise exception


# Setup the base class that all of the SQL objects will inherit from.
#
# Note that the typing hint is required to be set at Any for mypy to be cool
# with it being a base class. This should be fixed with SQLAlchemy2.0
#
# For more context:
# https://docs.sqlalchemy.org/en/14/orm/extensions/mypy.html
# https://github.com/python/mypy/issues/2477


class DatabaseManager:
    """
    manager class for rds application operations
    """

    def __init__(self, verbose: bool = False):
        """
        initialize db manager object, creates engine and sessionmaker
        """
        self.engine = get_local_engine(echo=verbose)

        sa.event.listen(
            self.engine,
            "do_connect",
            postgres_event_update_db_password,
        )

        self.session = sessionmaker(bind=self.engine)

    def get_session(self) -> sessionmaker:
        """
        get db session for performing actions
        """
        return self.session

    def execute(
        self,
        statement: Union[
            sa.sql.selectable.Select,
            sa.sql.dml.Update,
            sa.sql.dml.Delete,
            sa.sql.dml.Insert,
            sa.sql.elements.TextClause,
        ],
    ) -> sa.engine.CursorResult:
        """
        execute db action WITHOUT data
        """
        with self.session.begin() as cursor:
            result = cursor.execute(statement)
        return result  # type: ignore

    def select_as_list(self, select_query: sa.sql.selectable.Select) -> Union[List[Any], List[Dict[str, Any]]]:
        """
        select data from db table and return list
        """
        with self.session.begin() as cursor:
            return [row._asdict() for row in cursor.execute(select_query)]

    def write_to_csv(self, query: sa.sql.selectable.Select, dest_path: str, batch_size: int = 1024 * 1024) -> None:
        """
        stream db select results to csv file in batches

        :param query:       SQL Query to execute
        :param dest_path:   write location of csv file
        :param batch_size:  number of records per result partition of SQL query
        """
        header = None
        with self.session.begin() as cursor:
            result = cursor.execute(query).yield_per(batch_size)
            with open(dest_path, "w", newline="", encoding="utf8") as csv_file:
                for part in result.partitions():
                    rows = [row._asdict() for row in part]
                    if header is None:
                        header = list(rows[0].keys())
                        writer = csv.DictWriter(csv_file, fieldnames=header, quoting=csv.QUOTE_NONNUMERIC)
                        writer.writeheader()
                    writer.writerows(rows)

    def vaccuum_analyze(self, table: str) -> None:
        """RUN VACUUM (ANALYZE) on table"""
        with self.session.begin() as cursor:
            cursor.execute(sa.text("END TRANSACTION;"))
            cursor.execute(sa.text(f"VACUUM (ANALYZE) {table};"))

    def truncate_table(
        self,
        table_to_truncate: str,
        restart_identity: bool = False,
        cascade: bool = False,
    ) -> None:
        """
        truncate db table

        :param restart_identity: Restart sequences owned by columns of the truncated table(s).
        :param cascade:          Truncate all tables that have foreign-key relations to any of the named tables,
                                 or to any tables added to the group due to CASCADE.
        """
        truncate_query = f"TRUNCATE {table_to_truncate}"

        if restart_identity:
            truncate_query = f"{truncate_query} RESTART IDENTITY"

        if cascade:
            truncate_query = f"{truncate_query} CASCADE"

        self.execute(sa.text(f"{truncate_query};"))

        # Execute VACUUM to avoid non-deterministic behavior during testing
        self.vaccuum_analyze(table_to_truncate)


def copy_gzip_csv_to_db(local_path: str, destination_table: str) -> None:
    """
    load local csv (or csv.gz) file into DB using psql COPY command

    table headers are required to be in first row of file

    will throw if psql command does not exit with code 0

    :param local_path:          path to local file that will be loaded
    :param destination_table:   table name for COPY destination
    """
    copy_log = ProcessLogger(
        "gzip_psql_copy",
        local_file=local_path,
        destination_table=destination_table,
    )

    copy_from = f"FROM PROGRAM 'gzip -dc {local_path}' "
    if local_path.lower().endswith(".gz"):
        with gzip.open(local_path, "rt") as gzip_file:
            local_columns = gzip_file.readline().strip().lower().split(",")
    else:
        copy_from = f"FROM {local_path}"
        with open(local_path, "rt", encoding="utf8") as csv_file:
            local_columns = csv_file.readline().strip().lower().split(",")

    copy_command = f"\\COPY {destination_table} ({','.join(local_columns)}) {copy_from} WITH CSV HEADER"

    psql = [
        "psql",
        f"postgresql://{create_db_connection_string()}",
        "-c",
        f"{copy_command}",
    ]

    run_psql_subprocess(psql, copy_log)


def afc_copy(obj_path: str, destination_table: str, headers: List[str], null_as: bool = True) -> None:
    """
    load local csv or csv.gz file into DB using psql COPY command

    correct headers should be provided

    will throw if psql command does not exit with code 0

    :param local_path: path to local file that will be loaded
    :param destination_table: table name for COPY destination
    """
    copy_log = ProcessLogger(
        "psql_afc_copy",
        obj_path=obj_path,
        destination_table=destination_table,
        headers=" | ".join(headers),
    )

    copy_from = f"FROM {obj_path} "
    if obj_path.lower().startswith("s3://") and obj_path.lower().endswith(".gz"):
        copy_from = f"FROM PROGRAM 'aws s3 cp {obj_path} - | gzip -dc' "
    elif obj_path.lower().endswith(".gz"):
        copy_from = f"FROM PROGRAM 'gzip -dc {obj_path}' "

    null_as_str = "WITH NULL '\\N'"
    if not null_as:
        null_as_str = ""

    copy_command = f"\\COPY {destination_table} ({','.join(headers)}) {copy_from} {null_as_str} CSV QUOTE AS '\"'"

    psql = [
        "psql",
        f"postgresql://{create_db_connection_string()}",
        "-c",
        f"{copy_command}",
    ]

    run_psql_subprocess(psql, copy_log)


def zip_line_count(local_path: str) -> str:
    """
    get line count of local zip file

    :param local_path: path to local zip file

    :return number of lines in un-compressed zip file
    """
    output = subprocess.check_output(f"unzip -p {local_path} | wc -l", shell=True)

    return output.decode("utf8").strip()


def copy_zip_csv_to_db(local_path: str, destination_table: str) -> None:
    """
    load local csv.zip file into DB using psql COPY command

    table headers are required to be in first row of file
    file to load inside of zip archive should be same name as local path
    file without .zip

    will throw if psql command does not exit with code 0

    :param local_path: path to local file that will be loaded
    :param destination_table: table name for COPY destination
    """
    copy_log = ProcessLogger(
        "zip_psql_copy",
        local_file=local_path,
        destination_table=destination_table,
        row_count=zip_line_count(local_path),
    )

    with zipfile.ZipFile(local_path, "r") as zip_files:
        csv_file = zip_files.filelist[0].filename
        with zip_files.open(csv_file, "r") as reader:
            headers = reader.readline().decode().strip().lower().split(",")

    copy_log.add_metadata(csv_file=csv_file, headers="|".join(headers))

    copy_command = (
        f"\\COPY {destination_table} "
        f"({','.join(headers)}) "
        "FROM PROGRAM "
        f"'unzip -p {local_path}' "
        "WITH CSV HEADER"
    )

    psql = [
        "psql",
        f"postgresql://{create_db_connection_string()}",
        "-c",
        f"{copy_command}",
    ]

    run_psql_subprocess(psql, copy_log)


def run_psql_subprocess(psql_cmd: List[str], logger: ProcessLogger) -> None:
    """
    run psql command with retry logic
    """
    max_retries = 3
    logger.add_metadata(max_retries=max_retries)

    for retry_attempts in range(max_retries + 1):
        try:
            logger.add_metadata(retry_attempts=retry_attempts)
            process_result = subprocess.run(psql_cmd, check=True)
            break
        except Exception as exception:
            if retry_attempts == max_retries:
                logger.log_failure(exception=exception)
                raise exception
            time.sleep(5)

    logger.add_metadata(exit_code=process_result.returncode)
    logger.log_complete()
