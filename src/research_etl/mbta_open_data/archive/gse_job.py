import os
import tempfile
import shutil
import datetime

import sqlalchemy as sa

from research_etl.utils.util_rds import DatabaseManager
from research_etl.utils.util_logging import ProcessLogger


def run(db_manager: DatabaseManager) -> None:
    """Gated Station Entries Job"""
    process_log = ProcessLogger("etl_gse_csv")
    process_log.log_start()

    today = datetime.date.today()
    month_start = today.replace(day=1)

    query_end_date = month_start - datetime.timedelta(days=1)
    # last 3 years?
    query_start_date = month_start.replace(year=month_start.year - 3)

    query = f"""
        WITH gated1 AS (
            SELECT 
                servicedate as service_date
                ,CONCAT('(', RIGHT(halfhour::varchar, 8), ')') as time_period
                ,CASE 
                    WHEN stationname IN ('Alewife') THEN 'place-alfcl'
                    WHEN stationname IN ('Andrew') THEN 'place-andrw'
                    WHEN stationname IN ('Airport') THEN 'place-aport'
                    WHEN stationname IN ('Aquarium') THEN 'place-aqucl'
                    WHEN stationname IN ('Arlington') THEN 'place-armnl'
                    WHEN stationname IN ('Ashmont') THEN 'place-asmnl'
                    WHEN stationname IN ('Assembly') THEN 'place-astao'
                    WHEN stationname IN ('Back Bay') THEN 'place-bbsta'
                    WHEN stationname IN ('Beachmont') THEN 'place-bmmnl'
                    WHEN stationname IN ('Bowdoin') THEN 'place-bomnl'
                    WHEN stationname IN ('Boylston') THEN 'place-boyls'
                    WHEN stationname IN ('Broadway') THEN 'place-brdwy'
                    WHEN stationname IN ('Braintree') THEN 'place-brntn'
                    WHEN stationname IN ('Community College') THEN 'place-ccmnl'
                    WHEN stationname IN ('Charles/MGH') THEN 'place-chmnl'
                    WHEN stationname IN ('Chinatown') THEN 'place-chncl'
                    WHEN stationname IN ('Central') THEN 'place-cntsq'
                    WHEN stationname IN ('Copley') THEN 'place-coecl'
                    WHEN stationname IN ('Courthouse') THEN 'place-crtst'
                    WHEN stationname IN ('Davis') THEN 'place-davis'
                    WHEN stationname IN ('Downtown Crossing') THEN 'place-dwnxg'
                    WHEN stationname IN ('Fields Corner') THEN 'place-fldcr'
                    WHEN stationname IN ('Forest Hills') THEN 'place-forhl'
                    WHEN stationname IN ('Government Center') THEN 'place-gover'
                    WHEN stationname IN ('Green Street') THEN 'place-grnst'
                    WHEN stationname IN ('Haymarket') THEN 'place-haecl'
                    WHEN stationname IN ('Harvard') THEN 'place-harsq'
                    WHEN stationname IN ('Hynes Convention Center') THEN 'place-hymnl'
                    WHEN stationname IN ('Jackson Square') THEN 'place-jaksn'
                    WHEN stationname IN ('JFK/Umass') THEN 'place-jfk'
                    WHEN stationname IN ('Kenmore') THEN 'place-kencl'
                    WHEN stationname IN ('Kendall/MIT') THEN 'place-knncl'
                    WHEN stationname IN ('Lechmere') THEN 'place-lech'
                    WHEN stationname IN ('Massachusetts Ave.') THEN 'place-masta'
                    WHEN stationname IN ('Malden Center') THEN 'place-mlmnl'
                    WHEN stationname IN ('Maverick') THEN 'place-mvbcl'
                    WHEN stationname IN ('North Station') THEN 'place-north'
                    WHEN stationname IN ('North Quincy') THEN 'place-nqncy'
                    WHEN stationname IN ('Oak Grove') THEN 'place-ogmnl'
                    WHEN stationname IN ('Orient Heights') THEN 'place-orhte'
                    WHEN stationname IN ('Park Street') THEN 'place-pktrm'
                    WHEN stationname IN ('Porter') THEN 'place-portr'
                    WHEN stationname IN ('Prudential') THEN 'place-prmnl'
                    WHEN stationname IN ('Quincy Adams') THEN 'place-qamnl'
                    WHEN stationname IN ('Quincy Center') THEN 'place-qnctr'
                    WHEN stationname IN ('Revere Beach') THEN 'place-rbmnl'
                    WHEN stationname IN ('Roxbury Crossing') THEN 'place-rcmnl'
                    WHEN stationname IN ('Riverside') THEN 'place-river'
                    WHEN stationname IN ('Ruggles') THEN 'place-rugg'
                    WHEN stationname IN ('Stony Brook') THEN 'place-sbmnl'
                    WHEN stationname IN ('Suffolk Downs') THEN 'place-sdmnl'
                    WHEN stationname IN ('Savin Hill') THEN 'place-shmnl'
                    WHEN stationname IN ('Shawmut') THEN 'place-smmnl'
                    WHEN stationname IN ('Science Park') THEN 'place-spmnl'
                    WHEN stationname IN ('South Station') THEN 'place-sstat'
                    WHEN stationname IN ('State Street') THEN 'place-state'
                    WHEN stationname IN ('Sullivan Square') THEN 'place-sull'
                    WHEN stationname IN ('Symphony') THEN 'place-symcl'
                    WHEN stationname IN ('Tufts Medical Center') THEN 'place-tumnl'
                    WHEN stationname IN ('Wellington') THEN 'place-welln'
                    WHEN stationname IN ('Wood Island') THEN 'place-wimnl'
                    WHEN stationname IN ('Wollaston') THEN 'place-wlsta'
                    WHEN stationname IN ('Wonderland') THEN 'place-wondl'
                    WHEN stationname IN ('World Trade Center') THEN 'place-wtcst'
                END AS stop_id
                ,CASE 
                    WHEN stationname IN ('JFK/Umass') THEN 'JFK/UMass'
                    WHEN stationname IN ('Charles MGH') THEN 'Charles/MGH'
                    WHEN stationname IN ('Massachusetts Ave.') THEN 'Massachusetts Avenue'
                    ELSE stationname
                END AS station_name
                ,route_or_line
                ,CASE 
                    WHEN stationname IN ('Downtown Crossing', 'State Street', 'Haymarket', 'North Station', 'Government Center', 'South Station', 'Park Street')
                    THEN 1
                    ELSE 0
                END AS split_ind
                ,SUM(rawtaps_split) as gated_entries
            FROM 
                ridership.tableau_r r
            WHERE 
                route_or_line LIKE ('%Line')
                AND stationname NOT LIKE ('%Garage')
                AND r.servicedate >= '{query_start_date}'
                AND r.servicedate < '{query_end_date}'
            GROUP BY 
                1,2,3,4,5,6
            ORDER BY 
                1 DESC,2,3
        )
        SELECT
            service_date
            ,time_period
            ,stop_id
            ,station_name
            ,route_or_line
            ,CASE 
                WHEN split_ind = 1 
                THEN ROUND(gated_entries,2)
                ELSE gated_entries
            END as gated_entries
        FROM 
            gated1
        ;
    """
    temp_dir = tempfile.mkdtemp()
    export_file = f"{month_start.strftime('%Y-%m')}_GatedStationEntries.csv"
    export_path = os.path.join(temp_dir, export_file)

    process_log.add_metadata(export_path=export_path)
    try:
        # create CSV file from query
        db_manager.write_to_csv(sa.text(query), export_path)

        # TODO: send csv to Box? # pylint: disable=W0511

        process_log.log_complete()

    except Exception as exception:
        process_log.log_failure(exception)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    local_db = DatabaseManager()
    run(local_db)
