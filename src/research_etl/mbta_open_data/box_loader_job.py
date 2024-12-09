import os
import tempfile
from typing import Tuple
from datetime import datetime

from box_sdk_gen.schemas.file import File
from box_sdk_gen.schemas.folder_full import FolderFull
from box_sdk_gen.schemas.folder_base import FolderBaseTypeField

from research_etl.utils.box import BoxManager
from research_etl.utils.util_rds import copy_gzip_csv_to_db
from research_etl.utils.util_logging import ProcessLogger


BOX_IMPORT_FOLDER_ID = "287803137437"  # BoxAPI folder
ALLOWED_SCHEMAS = ("surveys","panel",)  # schemas this job can load into


def verify_import_folder(box_manager: BoxManager) -> Tuple[FolderFull, FolderFull]:
    """
    verify that BOX_IMPORT_FOLDER_ID contains "aws_loaded" and "aws_error" sub folders
    if they do not exist, create them

    :return: (aws_loaded_folder, aws_error_folder)
    """
    loaded = None
    error = None
    import_parent = box_manager.client.folders.get_folder_by_id(folder_id=BOX_IMPORT_FOLDER_ID)
    for item in box_manager.list_folder(folder_id=BOX_IMPORT_FOLDER_ID):
        if item.type != FolderBaseTypeField.FOLDER:
            continue
        if item.name == "aws_loaded":
            loaded = box_manager.client.folders.get_folder_by_id(folder_id=item.id)
        elif item.name == "aws_error":
            error = box_manager.client.folders.get_folder_by_id(folder_id=item.id)
        if loaded is not None and error is not None:
            break

    if loaded is None:
        loaded = box_manager.client.folders.create_folder(name="aws_loaded", parent=import_parent)
    if error is None:
        error = box_manager.client.folders.create_folder(name="aws_error", parent=import_parent)

    return (loaded, error)


def load_file_to_rds(box_manager: BoxManager, file: File) -> bool:
    """
    load file from box into RDS

    :return: True if load success, else False
    """
    logger = ProcessLogger("opmi_load_box_file", file_name=file.name, file_id=file.id)
    logger.log_start()

    try:
        schema, table_name = file.name.lower().replace(".csv", "").split("_", maxsplit=1)
        if schema not in ALLOWED_SCHEMAS:
            raise PermissionError(f"box_loader job not allowed to load into {schema} schema.")

        target_table = f"{schema}.{table_name}"
        logger.add_metadata(target_table=target_table)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "temp.csv")
            box_manager.download_file(file, temp_file)
            copy_gzip_csv_to_db(temp_file, target_table)
        logger.log_complete()

    except Exception as exception:
        logger.log_failure(exception)
        return False

    return True


def run() -> None:
    """
    Load files from Box folder into RDS tables

    Job steps:
     1. confirm structure of BOX_IMPORT_FOLDER_ID
        1.a BOX_IMPORT_FOLDER_ID should contain folder named "aws_loaded" (where sucessfully processed files will be moved to)
        1.b BOS_IMPORT_FOLDER_ID should contain folder named "aws_error" (where files with load errors will be moved to)
        1.c if either expected folder does not exist, create them
     2. Iterate through all .csv files in BOX_IMPORT_FOLDER_ID
        2.a Files should follow specific naming convention targetSchema_targetTable.csv
        2.b First row of file should be column names that match targetTable
     3. Download file to local disk from Box
     4. Load file into RDS targetSchema.targetTable via csv load function
        4.a On successful load, move file to "aws_loaded" folder
        4.b If load error occurs, move file to "aws_error" folder
    """
    job_logger = ProcessLogger("box_loader_job")
    job_logger.log_start()

    success_count = 0
    error_count = 0

    try:
        box_manager = BoxManager()
        success_folder, error_folder = verify_import_folder(box_manager)
        import_items = box_manager.list_folder(BOX_IMPORT_FOLDER_ID)
        job_logger.add_metadata(num_import_items=len(import_items))

        for item in import_items:
            if not item.name.endswith(".csv"):
                continue

            load_status = load_file_to_rds(box_manager, item)

            new_file_name = f"{datetime.now().isoformat()}_{item.name}"
            if load_status:
                # move to success folder
                success_count += 1
                box_manager.client.files.update_file_by_id(file_id=item.id, name=new_file_name, parent=success_folder)
            else:
                # move to error folder
                error_count += 1
                box_manager.client.files.update_file_by_id(file_id=item.id, name=new_file_name, parent=error_folder)

        job_logger.add_metadata(success_count=success_count, error_count=error_count)
        job_logger.log_complete()

    except Exception as exception:
        job_logger.log_failure(exception)
