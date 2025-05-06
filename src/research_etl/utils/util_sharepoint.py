import os
from dataclasses import dataclass
from typing import List
from typing import Any

import requests
from msal import ConfidentialClientApplication

from research_etl.utils.util_logging import ProcessLogger


@dataclass(init=False)
class DriveItem:
    """GraphAPI driveItem (partial implementation)"""

    id: str
    name: str
    size: int
    file: bool
    folder: bool

    def __init__(self, **kwargs):  # type: ignore
        self.id = kwargs["id"]
        self.name = kwargs["name"]
        self.size = kwargs["size"]
        self.file = "file" in kwargs
        self.folder = "folder" in kwargs


class SharePointManager:
    """
    Manager class for SharePoint file operations
    """

    def __init__(
        self,
        site_name: str,
        domain: str,
        tenant_id_var: str,
        client_id_var: str,
        client_secret_var: str,
    ):
        self.site_name = site_name
        self.domain = domain
        self.tenant_id = os.getenv(tenant_id_var, "")
        self.client_id = os.getenv(client_id_var, "")
        self.client_secret = os.getenv(client_secret_var, "")

        self.session = requests.Session()

        logger = ProcessLogger("init_sharepoint_manager", site_name=site_name, domain=domain)
        try:
            self.generate_headers()
            # Fetch the site ID from the site name
            site_url = f"https://graph.microsoft.com/v1.0/sites/{domain}:/sites/{site_name}"
            site_r = self.get_request(site_url)
            self.site_id = site_r.json()["id"]

            # Fetch the drive ID of the site Document Library
            drive_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive"
            drive_r = self.get_request(drive_url)
            self.drive_id = drive_r.json()["id"]
            self.drive_url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}"
            logger.log_complete()

        except Exception as exception:
            logger.log_failure(exception)
            raise exception

    def generate_headers(self) -> None:
        """Create authentication headers for GraphAPI calls."""
        # Build authority URL
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        # Create MSAL application
        app = ConfidentialClientApplication(
            client_id=self.client_id, client_credential=self.client_secret, authority=authority
        )
        # Request an access token
        token_response = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        headers = {"Authorization": f"Bearer {token_response['access_token']}"}
        self.session.headers.update(headers)

    def get_request(self, url: str) -> requests.Response:
        """Make GraphAPI GET requests"""
        logger = ProcessLogger("graph_get_request", url=url)
        try:
            r = self.session.get(url)
            r.raise_for_status()
            logger.log_complete()
            return r
        except Exception as exception:
            logger.add_metadata(response_content=r.content)
            logger.log_failure(exception)
            raise exception

    def patch_request(self, url: str, data: dict[str, Any] | None = None) -> requests.Response:
        """Make GraphAPI PATCH requests"""
        logger = ProcessLogger("graph_patch_request", url=url)
        try:
            r = self.session.patch(url, json=data)
            r.raise_for_status()
            logger.log_complete()
            return r
        except Exception as exception:
            logger.add_metadata(response_content=r.content)
            logger.log_failure(exception)
            raise exception

    def post_request(self, url: str, data: dict[str, Any] | None = None) -> requests.Response:
        """Make GraphAPI POST requests"""
        logger = ProcessLogger("graph_post_request", url=url)
        try:
            r = self.session.post(url, json=data)
            r.raise_for_status()
            logger.log_complete()
            return r
        except Exception as exception:
            logger.add_metadata(response_content=r.content)
            logger.log_failure(exception)
            raise exception

    def list_folder(self, folder_path: str, limit: int = 1000) -> List[DriveItem]:
        """
        Retrieve a list of items (files/folders) from a Sharepoint folder by path.

        :param folder_path: Sharepoint drive path
        :param limit: maximum number of items to return.

        :return: List of items in folder_path as DriveItem
        """
        folder_path = folder_path.rstrip("/")
        logger = ProcessLogger("sp_list_folder", folder_path=folder_path)
        items = []
        try:
            url = f"{self.drive_url}/root:/{folder_path}:/children?$top={limit}"
            resp = self.get_request(url)
            items = resp.json().get("value", [])
            logger.log_complete(folder_item_count=len(items))
            return [DriveItem(**i) for i in items]
        except Exception as ex:
            logger.log_failure(ex)
            raise ex

    def download_item(self, item_id: str, local_path: str) -> None:
        """
        Download sharepoint file by item_id.

        :param item_id: sharepoint id of file to download
        :param local_path: local path file will be saved to
        """
        logger = ProcessLogger("sp_download_item", item_id=item_id, local_path=local_path)

        try:
            # Build URL: GET /sites/{site_id}/drive/root:/{file_path}:/content
            url = f"{self.drive_url}/items/{item_id}/content"
            resp = self.get_request(url)
            with open(local_path, "wb") as writer:
                writer.write(resp.content)
            logger.log_complete()

        except Exception as ex:
            logger.log_failure(ex)
            raise ex

    def get_item_by_path(self, item_path: str) -> DriveItem:
        """
        Get DriveItem info from a sharepoint item by path.

        :param item_path: Sharepoint drive path

        :return: DriveItem information for item_path
        """
        url = f"{self.drive_url}/root:/{item_path}"
        resp = self.get_request(url)
        return DriveItem(**resp.json())

    def create_subfolder(self, parent_folder_id: str, folder_name: str) -> DriveItem:
        """
        Creates a new sharepoint folder.

        :param parent_folder_id: Sharepoint ID of folder to create subfolder in
        :param folder_name: Name of new folder

        :return: DriveItem infomration for newly created folder
        """
        url = f"{self.drive_url}/items/{parent_folder_id}/children"
        data = {
            "name": folder_name,
            "folder": {},  # indicates creation of a folder
        }
        resp = self.post_request(url, data=data)
        return DriveItem(**resp.json())

    def move_item(self, item_id: str, new_folder_id: str, new_file_name: str = "") -> DriveItem:
        """
        Move a sharepoint item to a new folder.

        :param item_id: sharepoint ID of item to move
        :param new_folder_id: sharepoint ID of folder to move item into
        :param new_file_name: (Optional) new name for item in new folder

        :return: DriveItem information for moved item
        """
        url = f"{self.drive_url}/items/{item_id}"
        data = {"parentReference": {"id": new_folder_id}}
        if new_file_name != "":
            data["name"] = new_file_name  # type: ignore
        resp = self.patch_request(url, data=data)
        return DriveItem(**resp.json())
