import os
import json
from typing import Optional
from typing import Union
from typing import List

from box_sdk_gen import JWTConfig
from box_sdk_gen import BoxJWTAuth
from box_sdk_gen import BoxClient
from box_sdk_gen.schemas.file_full import FileFull
from box_sdk_gen.schemas.folder_mini import FolderMini
from box_sdk_gen.schemas.web_link import WebLink
from box_sdk_gen.schemas.file import File

from research_etl.utils.util_logging import ProcessLogger


class BoxManager:
    """
    manager class for Box file operations
    """

    def __init__(self, jwt_env_var: str = "OPMI_BOX_JWT"):
        """
        initialize box manager object
        authenticates via JWT and creates box client

        :param jwt_env_var: ENV VAR name to pull Box JWT from
        """
        logger = ProcessLogger("box_manager")

        try:
            config_as_dict = json.loads(str(os.getenv(jwt_env_var)), strict=False)
            jwt_config = JWTConfig.from_config_json_string(json.dumps(config_as_dict))
            auth = BoxJWTAuth(jwt_config)
            self.client = BoxClient(auth)
            logger.log_complete()
        except Exception as exception:
            logger.log_failure(exception)
            raise exception

    def list_folder(
        self, folder_id: str = "0", limit: int = 1_000
    ) -> Optional[List[Union[FileFull, FolderMini, WebLink]]]:
        """
        retrieve a list of items from a folder
        by default returns 1_000 items in the folder

        This function does not do pagination of results (which is possible) for very large folders

        :param folder_id: Box folder_id to list, default to "0" which should be Box Account root folder
        :param limit: Maximum number of items to return as list
        """
        logger = ProcessLogger("box_list_folder")

        try:
            items = self.client.folders.get_folder_items(folder_id, limit=limit)
            logger.add_metadata(total_count=items.total_count)
            logger.log_complete()
        except Exception as exception:
            logger.log_failure(exception)
            raise exception

        return items.entries

    def download_file(self, file: File, local_path: str) -> None:
        """
        download box file to local path

        This function does not write in chunks, which could be an issue for very large files...

        :param file: Box File to be downloaded
        :param local_path: local path that Box file will be downloaded to

        :return True if download success, else False
        """
        logger = ProcessLogger("box_download_file", file_name=file.name, local_path=local_path)

        try:
            with open(local_path, "wb") as writer:
                writer.write(self.client.downloads.download_file(file.id).read())
            logger.log_complete()

        except Exception as exception:
            logger.log_failure(exception)
            raise exception
