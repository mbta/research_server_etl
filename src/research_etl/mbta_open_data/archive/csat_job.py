import os
import tempfile
import shutil
import datetime

import sqlalchemy as sa

from research_etl.utils.util_rds import DatabaseManager
from research_etl.utils.util_logging import ProcessLogger


def run(db_manager: DatabaseManager) -> None:
    """CSAT Job"""
    process_log = ProcessLogger("etl_csat_csv")
    process_log.log_start()

    today = datetime.date.today()
    # start of prior month
    prev_month_start = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)

    query = """
        SELECT DISTINCT 
            survey_date
            ,survey_name
            ,question_description
            ,response_total
            ,response_1_text
            ,round(response_1_percent, 2) AS response_1_percent
            ,response_2_text
            ,round(response_2_percent, 2) AS response_2_percent
            ,response_3_text
            ,round(response_3_percent, 2) AS response_3_percent
            ,response_4_text
            ,round(response_4_percent, 2) AS response_4_percent 
            ,response_5_text 
            ,round(response_5_percent, 2) AS response_5_percent 
            ,response_6_text 
            ,round(response_6_percent, 2) AS response_6_percent 
            ,response_7_text
            ,round(response_7_percent, 2) AS response_7_percent 
        FROM 
            surveys.dashboard_survey_result_archive r 
        LEFT JOIN 
            surveys.dashboard_survey_response_type_archive t 
        ON 
            r.response_type_id = t.response_type_id 
        LEFT JOIN 
            surveys.dashboard_survey_questions_archive q 
        ON 
            r.question_id = q.question_id 
        WHERE 
            r.archive_time = (SELECT max(archive_time) FROM surveys.dashboard_survey_result_archive)
            AND r.question_id IN (3, 4, 10, 31) 
        ORDER BY 
            survey_date
        ;
    """
    temp_dir = tempfile.mkdtemp()
    export_file = f"{prev_month_start.strftime('%Y-%m')}_csat.csv"
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
