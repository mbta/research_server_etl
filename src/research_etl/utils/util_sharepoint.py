import os
import json
import requests
import io
import pandas as pd
from msal import ConfidentialClientApplication
from typing import Optional, List, Any, Dict

from research_etl.utils.util_logging import ProcessLogger

class SharePointManager:
    """
    Manager class for SharePoint file operations
    """

    def __init__(
        self,
        tenant_id_env_var: str = "OPMI_SHAREPOINT_TENANT",
        client_id_env_var: str = "OPMI_SHAREPOINT_CLIENT",
        client_secret_env_var: str = "OPMI_SHAREPOINT_SECRET",
    ):

        self.logger = ProcessLogger("sharepoint_manager")
        self.logger.log_start()

        try:
            tenant_id = os.getenv(tenant_id_env_var)
            client_id = os.getenv(client_id_env_var)
            client_secret = os.getenv(client_secret_env_var)
            site_name = "OPMI"
            domain = "mbta.sharepoint.com"

            # Build authority URL
            authority = f"https://login.microsoftonline.com/{tenant_id}"

            # Create MSAL application
            self.app = ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=authority
            )

            # Request an access token
            scopes = ["https://graph.microsoft.com/.default"]
            token_response = self.app.acquire_token_for_client(scopes=scopes)
            if "access_token" not in token_response:
                raise Exception(
                    f"Could not retrieve access token! Error: {token_response.get('error_description')}"
                )

            self.access_token = token_response["access_token"]
            self.headers = {"Authorization": f"Bearer {self.access_token}"}

            # Fetch the site ID from the site name
            site_url = f"https://graph.microsoft.com/v1.0/sites/{domain}:/sites/{site_name}"
            site_resp = requests.get(site_url, headers=self.headers)
            site_resp.raise_for_status()
            site_data = site_resp.json()
            self.site_id = site_data["id"]

            self.logger.log_complete()

        except Exception as ex:
            self.logger.log_failure(ex)
            raise ex

    def list_folder(self, folder_path: str, limit: int = 1000) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves a list of items (files/folders) from a given SharePoint folder

        return a list of item metadata dictionaries, or None if an error occurs
        """
        logger = ProcessLogger("sharepoint_list_folder", folder_path=folder_path)
        logger.log_start()

        try:
            # Build URL: GET /sites/{site_id}/drive/root:/{folder_path}:/children?$top={limit}
            url = (
                f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root:"
                f"/{folder_path}:/children?$top={limit}"
            )
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("value", [])
            logger.add_metadata(total_count=len(items))
            logger.log_complete()
            return items
        except Exception as ex:
            logger.log_failure(ex)
            raise ex

    def download_file(self, file_path: str, local_path: str) -> None:
        """
        Downloads a file from SharePoint to a specified local path.
        """
        logger = ProcessLogger("sharepoint_download_file", file_path=file_path, local_path=local_path)
        logger.log_start()

        try:
            # Build URL: GET /sites/{site_id}/drive/root:/{file_path}:/content
            url = (
                f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root:"
                f"/{file_path}:/content"
            )
            resp = requests.get(url, headers=self.headers, stream=True)
            resp.raise_for_status()

            with open(local_path, "wb") as writer:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        writer.write(chunk)

            logger.log_complete()

        except Exception as ex:
            logger.log_failure(ex)
            raise ex

    def get_item_by_path(self, item_path: str) -> dict:
        """
        Retrieves metadata for a file or a folder by relative path.

        returns the item’s metadata dictionary (including 'id' and 'name').
        """
        self._ensure_drive_id()
        # GET /drives/{drive-id}/root:/{item_path}
        url = (
            f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}"
            f"/root:/{item_path}"
        )
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def create_subfolder(self, parent_folder_id: str, new_folder_name: str) -> dict:
        """
        Creates a new folder under the given parent folder ID.

        returns the new folder’s metadata
        """
        url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{parent_folder_id}/children"
        body = {
            "name": new_folder_name,
            "folder": {}  # indicates creation of a folder
        }
        resp = requests.post(url, headers=self.headers, json=body)
        resp.raise_for_status()
        return resp.json()

    def move_file(self, file_id: str, new_folder_id: str, new_file_name: str) -> dict:
        """
        Moves (and rename if needed) a file to a new folder in SharePoint.

        returns the updated file’s metadata
        """
        self._ensure_drive_id()
        url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{file_id}"
        body = {
            "name": new_file_name,
            "parentReference": {
                "id": new_folder_id
            }
        }
        resp = requests.patch(url, headers=self.headers, json=body)
        resp.raise_for_status()
        return resp.json()