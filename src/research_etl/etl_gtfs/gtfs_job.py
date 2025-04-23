import re
import datetime
import zipfile

from typing import Tuple
from typing import Optional
from io import BytesIO
from http.client import HTTPMessage
import urllib.request

import polars
import sqlalchemy as sa

from research_etl.utils.util_rds import DatabaseManager
from research_etl.utils.util_rds import create_db_connection_string
from research_etl.utils.util_logging import ProcessLogger

from research_etl.etl_gtfs.gtfs_schema import GTFSSchema
from research_etl.etl_gtfs.gtfs_schema import feed_info_schema
from research_etl.etl_gtfs.gtfs_schema import agency_schema
from research_etl.etl_gtfs.gtfs_schema import calendar_schema
from research_etl.etl_gtfs.gtfs_schema import calendar_attributes_schema
from research_etl.etl_gtfs.gtfs_schema import calendar_dates_schema
from research_etl.etl_gtfs.gtfs_schema import checkpoints_schema
from research_etl.etl_gtfs.gtfs_schema import directions_schema
from research_etl.etl_gtfs.gtfs_schema import facilities_schema
from research_etl.etl_gtfs.gtfs_schema import facilities_properties_schema
from research_etl.etl_gtfs.gtfs_schema import levels_schema
from research_etl.etl_gtfs.gtfs_schema import lines_schema
from research_etl.etl_gtfs.gtfs_schema import multi_route_trips_schema
from research_etl.etl_gtfs.gtfs_schema import pathways_schema
from research_etl.etl_gtfs.gtfs_schema import route_patterns_schema
from research_etl.etl_gtfs.gtfs_schema import routes_schema
from research_etl.etl_gtfs.gtfs_schema import shapes_schema
from research_etl.etl_gtfs.gtfs_schema import stop_times_schema
from research_etl.etl_gtfs.gtfs_schema import stops_schema
from research_etl.etl_gtfs.gtfs_schema import transfers_schema
from research_etl.etl_gtfs.gtfs_schema import trips_schema


DB_GTFS_SCHEMA = "gtfs"

TABLES_TO_LOAD = [
    GTFSSchema(
        table_name="agency",
        schema=agency_schema,
        primary_keys=["agency_id"],
    ),
    GTFSSchema(
        table_name="calendar",
        schema=calendar_schema,
        primary_keys=["service_id"],
        to_date_fields=[
            "start_date",
            "end_date",
        ],
    ),
    GTFSSchema(
        table_name="calendar_attributes",
        schema=calendar_attributes_schema,
        primary_keys=["service_id"],
    ),
    GTFSSchema(
        table_name="calendar_dates",
        schema=calendar_dates_schema,
        primary_keys=[
            "service_id",
            "date",
        ],
        to_date_fields=[
            "date",
        ],
    ),
    GTFSSchema(
        table_name="checkpoints",
        schema=checkpoints_schema,
        primary_keys=["checkpoint_id"],
    ),
    GTFSSchema(
        table_name="directions",
        schema=directions_schema,
        primary_keys=[
            "route_id",
            "direction_id",
        ],
    ),
    GTFSSchema(
        table_name="facilities",
        schema=facilities_schema,
        primary_keys=["facility_id"],
    ),
    GTFSSchema(
        table_name="facilities_properties",
        schema=facilities_properties_schema,
        primary_keys=[],
    ),
    GTFSSchema(
        table_name="levels",
        schema=levels_schema,
        primary_keys=["level_id"],
    ),
    GTFSSchema(
        table_name="lines",
        schema=lines_schema,
        primary_keys=["line_id"],
    ),
    GTFSSchema(
        table_name="multi_route_trips",
        schema=multi_route_trips_schema,
        primary_keys=[
            "added_route_id",
            "trip_id",
        ],
    ),
    GTFSSchema(table_name="pathways", schema=pathways_schema, primary_keys=["pathway_id"]),
    GTFSSchema(table_name="route_patterns", schema=route_patterns_schema, primary_keys=["route_pattern_id"]),
    GTFSSchema(
        table_name="routes",
        schema=routes_schema,
        primary_keys=["route_id"],
    ),
    GTFSSchema(
        table_name="shapes",
        schema=shapes_schema,
        primary_keys=[
            "shape_id",
            "shape_pt_sequence",
        ],
    ),
    GTFSSchema(
        table_name="stop_times",
        schema=stop_times_schema,
        primary_keys=[
            "trip_id",
            "stop_sequence",
        ],
    ),
    GTFSSchema(
        table_name="stops",
        schema=stops_schema,
        primary_keys=["stop_id"],
    ),
    GTFSSchema(
        table_name="transfers",
        schema=transfers_schema,
        primary_keys=[],
    ),
    GTFSSchema(
        table_name="trips",
        schema=trips_schema,
        primary_keys=["trip_id"],
    ),
]


def download_gtfs() -> Tuple[BytesIO, HTTPMessage]:
    """
    Download MBTA GTFS zip file from https://cdn.mbta.com/MBTA_GTFS.zip

    Args:
        None

    Returns:
        BytesIO: GTFS Zip file as Bytes object in memory
        HTTPMessage: HTTP Header from GTFS Zip download
    """
    gtfs_url = "https://cdn.mbta.com/MBTA_GTFS.zip"

    with urllib.request.urlopen(gtfs_url) as req:
        gtfs_headers = req.headers
        gtfs_bytes = BytesIO(req.read())

    return (gtfs_bytes, gtfs_headers)


def last_feed_version(db_manager: DatabaseManager) -> Optional[str]:
    """
    Retrieve last added GTFS Feed Version from RDS

    Args:
        None

    Returns:
        str: feed version string
    """
    query = "SELECT feed_version " f"FROM {DB_GTFS_SCHEMA}.feed_info " "ORDER BY creation_timestamp DESC " "LIMIT 1"

    result = db_manager.select_as_list(sa.text(query))

    if result:
        return db_manager.select_as_list(sa.text(query))[0]["feed_version"]

    return None


def str_col_to_date(df: polars.DataFrame, column: str, date_format: str = "%Y%m%d") -> polars.DataFrame:
    """
    convert polars string series to date type

    Args:
        df (polars.Dataframe): Dataframe with column
        column (str): Name of column to convert
        date_format (str) = %Y%m%d: format of date string

    Returns:
        polars.Dataframe: dataframe with converted column
    """
    return df.with_columns(df[column].str.to_date(format=date_format).alias(column))


def partition_table_name(table: str, start: datetime.date, end: datetime.date) -> str:
    """
    create partitioned table name based on start/end dates
    """
    return f"{DB_GTFS_SCHEMA}.{table}_" f"{str(start).replace('-','')}_" f"{str(end).replace('-','')}"


def process_feed_info(gtfs_bytes: BytesIO) -> Tuple[datetime.date, datetime.date]:
    """
    Process feed_info.text file from GTFS and INSERT into Database

    Args:
        gtfs_bytes (BytesIO): Bytes of GTFS file in memory

    Returns:
        feed_start_date (datetime.date)
        feed_end_date (datetime.date)
    """
    with zipfile.ZipFile(gtfs_bytes) as gtfs_zip:
        feed_info_df = polars.read_csv(
            gtfs_zip.read("feed_info.txt"), schema_overrides=feed_info_schema, columns=list(feed_info_schema.keys())
        )

    # Extract creation_timestamp from feed_version text
    feed_version_dt_re = re.search(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        feed_info_df["feed_version"][0],
    )
    assert feed_version_dt_re is not None

    feed_version_dt_str = feed_version_dt_re.group(0)
    assert feed_version_dt_str is not None

    feed_version_dt = datetime.datetime.fromisoformat(feed_version_dt_str)

    feed_info_df = feed_info_df.with_columns(creation_timestamp=feed_version_dt)

    # convert date strings to datime.date types
    feed_info_df = str_col_to_date(feed_info_df, "feed_start_date")
    feed_info_df = str_col_to_date(feed_info_df, "feed_end_date")

    # pull valid dates
    valid_start_date = feed_info_df["feed_start_date"][0]
    valid_end_date = feed_info_df["feed_end_date"][0]

    feed_info_df = feed_info_df.with_columns(valid_start_date=valid_start_date)
    feed_info_df = feed_info_df.with_columns(valid_end_date=valid_end_date)

    feed_info_df.write_database(
        table_name=f"{DB_GTFS_SCHEMA}.feed_info",
        connection=f"postgresql+psycopg2://{create_db_connection_string()}",
        if_table_exists="append",
    )

    return (valid_start_date, valid_end_date)


def load_gtfs_table(
    db_manager: DatabaseManager,
    gtfs_bytes: BytesIO,
    table: GTFSSchema,
    valid_start_date: datetime.date,
    valid_end_date: datetime.date,
) -> None:
    """
    Load a GTFS table
    """
    load_log = ProcessLogger("load_gtfs_table", table_name=table.table_name)

    with zipfile.ZipFile(gtfs_bytes) as gtfs_zip:
        table_df = polars.read_csv(
            gtfs_zip.read(f"{table.table_name}.txt"), schema_overrides=table.schema, columns=list(table.schema.keys())
        )

    # change string date fields to datetime.date
    for column in table.to_date_fields:
        table_df = str_col_to_date(table_df, column)

    # add valid date columns to tables
    table_df = table_df.with_columns(valid_start_date=valid_start_date)
    table_df = table_df.with_columns(valid_end_date=valid_end_date)

    main_table = f"{DB_GTFS_SCHEMA}.{table.table_name}"
    new_table_name = partition_table_name(table.table_name, valid_start_date, valid_end_date)

    load_log.add_metadata(
        new_table_name=new_table_name,
        valid_start_date=valid_start_date,
        valid_end_date=valid_end_date,
    )

    create_table_query = f"CREATE TABLE {new_table_name} () INHERITS ({main_table})"
    db_manager.execute(sa.text(create_table_query))

    table_df.write_database(
        table_name=new_table_name,
        connection=f"postgresql+psycopg2://{create_db_connection_string()}",
        if_table_exists="append",
    )

    primary_key = ""
    if len(table.primary_keys) > 0:
        primary_key = f"ADD PRIMARY KEY ({', '.join(table.primary_keys)}),"

    alter_query = (
        f"ALTER TABLE {new_table_name} "
        f"{primary_key}"
        f"ADD CHECK (valid_start_date = '{valid_start_date}'),"
        f"ADD CHECK (valid_end_date = '{valid_end_date}')"
    )
    db_manager.execute(sa.text(alter_query))

    load_log.log_complete()


def build_shapes_geog(
    db_manager: DatabaseManager, valid_start_date: datetime.date, valid_end_date: datetime.date
) -> None:
    """
    Create shapes_geog table
    """
    build_log = ProcessLogger("build_shapes_geog")

    main_table = f"{DB_GTFS_SCHEMA}.shapes_geog"
    new_table_name = partition_table_name("shapes_geog", valid_start_date, valid_end_date)

    shapes_table = partition_table_name("shapes", valid_start_date, valid_end_date)

    create_table_query = f"CREATE TABLE {new_table_name} () INHERITS ({main_table})"
    db_manager.execute(sa.text(create_table_query))

    insert_query = (
        f"INSERT INTO {new_table_name} "
        "SELECT shape_id"
        ",ST_MakeLine(array_agg(ST_GeomFromText('POINT(' || shape_pt_lon || ' ' || shape_pt_lat || ')', 4326) ORDER BY shape_pt_sequence))"
        ",valid_start_date, valid_end_date "
        f"FROM {shapes_table} "
        "GROUP BY shape_id, valid_start_date, valid_end_date "
        "ORDER BY shape_id "
    )
    db_manager.execute(sa.text(insert_query))

    alter_query = (
        f"ALTER TABLE {new_table_name} "
        f"ADD PRIMARY KEY (shape_id),"
        f"ADD CHECK (valid_start_date = '{valid_start_date}'),"
        f"ADD CHECK (valid_end_date = '{valid_end_date}')"
    )
    db_manager.execute(sa.text(alter_query))

    build_log.log_complete()


def build_stops_geog(
    db_manager: DatabaseManager, valid_start_date: datetime.date, valid_end_date: datetime.date
) -> None:
    """
    Create stops_geog table
    """
    build_log = ProcessLogger("build_stops_geog")

    main_table = f"{DB_GTFS_SCHEMA}.stops_geog"
    new_table_name = partition_table_name("stops_geog", valid_start_date, valid_end_date)

    stops_table = partition_table_name("stops", valid_start_date, valid_end_date)

    create_table_query = f"CREATE TABLE {new_table_name} () INHERITS ({main_table})"
    db_manager.execute(sa.text(create_table_query))

    insert_query = (
        f"INSERT INTO {new_table_name} "
        "SELECT stop_id, parent_station "
        ", ST_GeogFromText('SRID=4326;POINT(' || stop_lon || ' ' || stop_lat || ')') "
        ", ST_GeomFromText('POINT(' || stop_lon || ' ' || stop_lat || ')', 4326) "
        ", CASE WHEN stop_lon::decimal BETWEEN -74.0000000 and -69.0000000 "
        "         AND stop_lat::decimal BETWEEN 41.0000000 and 43.0000000 "
        "       THEN (st_x(st_transform(st_geomFromText( "
        "             'POINT(' || stop_lon || ' ' || stop_lat || ')', "
        "             4326), 3585)) * 1000)::int "
        "       ELSE null END X "
        ", CASE WHEN stop_lon::decimal BETWEEN -74.0000000 and -69.0000000 "
        "         AND stop_lat::decimal BETWEEN 41.0000000 and  43.0000000 "
        "       THEN (st_y(st_transform(st_geomFromText( "
        "             'POINT(' || stop_lon || ' ' || stop_lat || ')', "
        "             4326), 3585)) * 1000)::int "
        "       ELSE null END Y "
        ", valid_start_date, valid_end_date "
        f"FROM {stops_table} "
        "ORDER BY stop_id "
    )
    db_manager.execute(sa.text(insert_query))

    alter_query = (
        f"ALTER TABLE {new_table_name} "
        f"ADD PRIMARY KEY (stop_id),"
        f"ADD CHECK (valid_start_date = '{valid_start_date}'),"
        f"ADD CHECK (valid_end_date = '{valid_end_date}')"
    )
    db_manager.execute(sa.text(alter_query))

    build_log.log_complete()


def build_stops_in_pattern(
    db_manager: DatabaseManager, valid_start_date: datetime.date, valid_end_date: datetime.date
) -> None:
    """
    Create stop_in_pattern table
    """
    build_log = ProcessLogger("build_stops_in_pattern")

    main_table = f"{DB_GTFS_SCHEMA}.stop_in_pattern"
    new_table_name = partition_table_name("stop_in_pattern", valid_start_date, valid_end_date)

    shapes_table = partition_table_name("shapes_geog", valid_start_date, valid_end_date)
    trips_table = partition_table_name("trips", valid_start_date, valid_end_date)
    routes_table = partition_table_name("routes", valid_start_date, valid_end_date)
    stop_times_table = partition_table_name("stop_times", valid_start_date, valid_end_date)
    stops_geog_table = partition_table_name("stops_geog", valid_start_date, valid_end_date)

    create_table_query = f"CREATE TABLE {new_table_name} () INHERITS ({main_table})"
    db_manager.execute(sa.text(create_table_query))

    insert_query = (
        f"INSERT INTO {new_table_name} "
        "SELECT  shg.shape_id, st.stop_sequence, st.stop_id "
        ",(ST_LineLocatePoint(shape, geom) * ST_Length(ST_Transform(shape,26986)))::INT "
        ",shg.valid_start_date, shg.valid_end_date "
        f"FROM {shapes_table} shg "
        "INNER JOIN ( "
        "        SELECT shape_id, min(trip_id) trip_id, min(route_id) route_id "
        f"       FROM {trips_table} "
        "        GROUP BY shape_id "
        ") t ON t.shape_id = shg.shape_id "
        f"INNER JOIN {routes_table} r "
        "        ON r.route_id = t.route_id "
        "        AND r.route_type = 3 "  # bus only
        f"INNER JOIN {stop_times_table} st "
        "        ON st.trip_id = t.trip_id "
        f"INNER JOIN {stops_geog_table} stg "
        "        ON stg.stop_id = st.stop_id "
        "ORDER BY shg.shape_id, st.stop_sequence "
    )
    db_manager.execute(sa.text(insert_query))

    alter_query = (
        f"ALTER TABLE {new_table_name} "
        f"ADD PRIMARY KEY (shape_id, stop_sequence),"
        f"ADD CHECK (valid_start_date = '{valid_start_date}'),"
        f"ADD CHECK (valid_end_date = '{valid_end_date}')"
    )
    db_manager.execute(sa.text(alter_query))

    build_log.log_complete()


def run(db_manager: DatabaseManager) -> None:
    """
    main job event loop

    pull the most recent available GTFS schedule and compare feed_version to
    most recent feed version in research server

    if feed_version's do not match, load GTFS schedule
    """
    process_logger = ProcessLogger("etl_gtfs")
    try:
        gtfs_bytes, gtfs_headers = download_gtfs()

        # current GTFS feed_version provided as header metadata from file download
        download_feed_version = gtfs_headers.get("x-amz-meta-feed-version")

        db_feed_version = last_feed_version(db_manager)

        process_logger.add_metadata(
            rds_last_version=db_feed_version,
            download_version=download_feed_version,
        )

        # Do not run job if downloaded feed version is already in DB
        if download_feed_version == db_feed_version:
            process_logger.log_complete()
            return

        # Begin running GTFS ETL if downloaded feed is not in DB
        valid_start_date, valid_end_date = process_feed_info(gtfs_bytes)

        process_logger.add_metadata(
            valid_end_date=valid_end_date,
            valid_start_date=valid_start_date,
        )

        # load tables from GTFS file
        for table in TABLES_TO_LOAD:
            load_gtfs_table(
                db_manager,
                gtfs_bytes,
                table,
                valid_start_date,
                valid_end_date,
            )

        # build postgis tables from GTFS data
        # these were pulled from original ETL code on MIT Research Server
        build_shapes_geog(db_manager, valid_start_date, valid_end_date)
        build_stops_geog(db_manager, valid_start_date, valid_end_date)
        build_stops_in_pattern(db_manager, valid_start_date, valid_end_date)

        process_logger.log_complete()

    except Exception as exception:
        process_logger.log_failure(exception)


if __name__ == "__main__":
    local_db = DatabaseManager()
    run(local_db)
