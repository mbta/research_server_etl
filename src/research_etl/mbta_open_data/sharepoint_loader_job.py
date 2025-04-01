import os
import tempfile
import requests
from typing import Tuple
from datetime import datetime

from research_etl.utils.util_sharepoint import SharePointManager
from research_etl.utils.util_rds import copy_gzip_csv_to_db
from research_etl.utils.util_logging import ProcessLogger


BOX_IMPORT_FOLDER_PATH = remote_file_path = "01 Admin/00 Data Strategy/Ongoing Activities/API_Files/"
ALLOWED_SCHEMAS = (  # schemas this job can load into
    "surveys",
    "panel",
)


def verify_import_folder(sp_manager: SharePointManager, import_folder_path: str) -> Tuple[str, str]:
    """
    Verify that the import_folder_path contains "aws_loaded" and "aws_error" subfolders.
    If they do not exist, create them.

    Returns (aws_loaded_folder_id, aws_error_folder_id).
    """
    logger = ProcessLogger("verify_import_folder", folder_path=import_folder_path)
    logger.log_start()

    try:
        parent_item = sp_manager.get_item_by_path(import_folder_path)
        parent_id = parent_item["id"]

        # List everything in the parent folder
        items_in_parent = sp_manager.list_folder(import_folder_path)
        loaded_folder_id = None
        error_folder_id = None

        for item in items_in_parent:
            if "folder" in item:
                if item["name"] == "aws_loaded":
                    loaded_folder_id = item["id"]
                elif item["name"] == "aws_error":
                    error_folder_id = item["id"]

            if loaded_folder_id and error_folder_id:
                break

        if not loaded_folder_id:
            created = sp_manager.create_subfolder(parent_folder_id=parent_id, new_folder_name="aws_loaded")
            loaded_folder_id = created["id"]
        if not error_folder_id:
            created = sp_manager.create_subfolder(parent_folder_id=parent_id, new_folder_name="aws_error")
            error_folder_id = created["id"]

        logger.log_complete()
        return (loaded_folder_id, error_folder_id)

    except Exception as ex:
        logger.log_failure(ex)
        raise ex


def load_file_to_rds(sp_manager: SharePointManager, parent_path: str, item: dict) -> bool:
    """
    Load a file from SharePoint into RDS.

    return: True if load success, else False
    """
    logger = ProcessLogger("opmi_load_sp_file", file_name=item["name"], file_id=item["id"])
    logger.log_start()

    try:
        file_name = item["name"]
        schema, table_name = file_name.lower().replace(".csv", "").split("_", maxsplit=1)
        if schema not in ALLOWED_SCHEMAS:
            raise PermissionError(f"SharePoint loader job not allowed to load into {schema} schema.")

        target_table = f"{schema}.{table_name}"
        logger.add_metadata(target_table=target_table)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "temp.csv")
            file_path = f"{parent_path}/{file_name}"
            sp_manager.download_file(file_path, temp_file)
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
    job_logger.log_start()

    success_count = 0
    error_count = 0

    try:
        sp_manager = SharePointManager()
        loaded_folder_id, error_folder_id = verify_import_folder(
            sp_manager, SHAREPOINT_IMPORT_FOLDER_PATH
        )

        import_items = sp_manager.list_folder(SHAREPOINT_IMPORT_FOLDER_PATH)
        job_logger.add_metadata(num_import_items=len(import_items))

        for item in import_items:
            # If not a file or does not end with .csv, skip
            if "file" not in item or not item["name"].endswith(".csv"):
                continue

            load_status = load_file_to_rds(sp_manager, SHAREPOINT_IMPORT_FOLDER_PATH, item)
            new_file_name = f"{datetime.now().isoformat()}_{item['name']}"

            if load_status:
                success_count += 1
                sp_manager.move_file(file_id=item["id"], new_folder_id=loaded_folder_id, new_file_name=new_file_name)
            else:
                error_count += 1
                sp_manager.move_file(file_id=item["id"], new_folder_id=error_folder_id, new_file_name=new_file_name)

        job_logger.add_metadata(success_count=success_count, error_count=error_count)
        job_logger.log_complete()

    except Exception as exception:
        job_logger.log_failure(exception)
