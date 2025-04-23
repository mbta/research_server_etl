import os

from research_etl.etl_korbato.korbato_job import alt_run as alt_odx_job

from research_etl.utils.util_aws import check_for_parallel_tasks
from research_etl.utils.util_rds import DatabaseManager


def run_jobs() -> None:
    """
    Run All ETL jobs
    """
    os.environ["SERVICE_NAME"] = "opmi_research_etl"

    check_for_parallel_tasks()

    db_manager = DatabaseManager()

    alt_odx_job(db_manager)


if __name__ == "__main__":
    run_jobs()
