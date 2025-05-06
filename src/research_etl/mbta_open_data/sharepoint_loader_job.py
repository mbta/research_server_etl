import os
import tempfile
from datetime import datetime
from typing import Tuple

from research_etl.utils.util_sharepoint import SharePointManager
from research_etl.utils.util_sharepoint import DriveItem
from research_etl.utils.util_rds import copy_gzip_csv_to_db
from research_etl.utils.util_logging import ProcessLogger


SHAREPOINT_IMPORT_FOLDER_PATH = "01 Admin/00 Data Strategy/Ongoing Activities/API_Files/"
ALLOWED_SCHEMAS = (  # schemas this job can load into
    "surveys",
    "panel",
)


def verify_import_folder(sp_manager: SharePointManager) -> Tuple[DriveItem, DriveItem]:
    """
    Verify that the import_folder_path contains "aws_loaded" and "aws_error" subfolders.
    If they do not exist, create them.

    Returns (aws_loaded_folder_id, aws_error_folder_id).
    """
    parent_item = sp_manager.get_item_by_path(SHAREPOINT_IMPORT_FOLDER_PATH)
    loaded = None
    error = None
    for item in sp_manager.list_folder(SHAREPOINT_IMPORT_FOLDER_PATH):
        if item.folder is False:
            continue
        if item.name == "aws_loaded":
            loaded = item
        elif item.name == "aws_error":
            error = item
        if loaded is not None and error is not None:
            break

    if loaded is None:
        loaded = sp_manager.create_subfolder(parent_item.id, "aws_loaded")
    if error is None:
        error = sp_manager.create_subfolder(parent_item.id, "aws_error")

    return (loaded, error)


def load_file_to_rds(sp_manager: SharePointManager, item: DriveItem) -> bool:
    """
    Load a file from SharePoint into RDS.

    return: True if load success, else False
    """
    logger = ProcessLogger("opmi_load_sp_file", file_name=item.name, file_id=item.id)
    try:
        schema, table_name = item.name.lower().replace(".csv", "").split("_", maxsplit=1)
        if schema not in ALLOWED_SCHEMAS:
            raise PermissionError(f"SharePoint loader job not allowed to load into {schema} schema.")

        target_table = f"{schema}.{table_name}"
        logger.add_metadata(target_table=target_table)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "temp.csv")
            sp_manager.download_item(item.id, temp_file)
            copy_gzip_csv_to_db(temp_file, target_table)

        logger.log_complete()
        return True

    except Exception as exception:
        logger.log_failure(exception)
        return False


def run() -> None:
    """
    Load files from SharePoint folder into RDS tables.

    Job steps:
     1. Confirm structure of SHAREPOINT_IMPORT_FOLDER_PATH:
        a) Folder should contain subfolder "aws_loaded" (for successfully processed files)
        b) Folder should contain subfolder "aws_error"  (for load-error files)
        c) If either subfolder does not exist, create it
     2. Iterate through all .csv files in SHAREPOINT_IMPORT_FOLDER_PATH
        a) Files must follow naming convention: schema_table.csv
        b) The first row is column names that match the target table
     3. Download file locally from SharePoint
     4. Load file into RDS (schema.table)
        a) On success, move file to "aws_loaded" folder
        b) On error, move file to "aws_error" folder
    """
    job_logger = ProcessLogger("sharepoint_loader_job")

    success_count = 0
    error_count = 0

    try:
        sp_manager = SharePointManager(
            site_name="OPMI",
            domain="mbta.sharepoint.com",
            tenant_id_var="OPMI_GRAPH_TENANT",
            client_id_var="OPMI_GRAPH_CLIENT",
            client_secret_var="OPMI_GRAPH_SECRET",
        )
        success_folder, error_folder = verify_import_folder(sp_manager)
        import_items = sp_manager.list_folder(SHAREPOINT_IMPORT_FOLDER_PATH)
        job_logger.add_metadata(num_import_items=len(import_items))

        for item in import_items:
            if not item.name.endswith(".csv"):
                continue

            load_status = load_file_to_rds(sp_manager, item)

            new_file_name = f"{datetime.now().isoformat()}_{item.name}"
            if load_status:
                success_count += 1
                sp_manager.move_item(item.id, success_folder.id, new_file_name=new_file_name)
            else:
                error_count += 1
                sp_manager.move_item(item.id, error_folder.id, new_file_name=new_file_name)

        job_logger.add_metadata(success_count=success_count, error_count=error_count)
        job_logger.log_complete()

    except Exception as exception:
        job_logger.log_failure(exception)
