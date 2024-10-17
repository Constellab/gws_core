

from typing import List, Optional

import requests
from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.utils.settings import Settings
from gws_core.model.typing_manager import TypingManager
from gws_core.share.share_link import ShareLink
from gws_core.share.shared_dto import (ShareResourceInfoReponseDTO,
                                       ShareResourceZippedResponseDTO)


class ResourceDownloader():
    """
    Class to download a resource from another lab
    """

    message_dispatcher: MessageDispatcher

    def __init__(self, message_dispatcher: Optional[MessageDispatcher] = None) -> None:

        if message_dispatcher is None:
            self.message_dispatcher = MessageDispatcher()
        else:
            self.message_dispatcher = message_dispatcher

    def check_compatiblity(self, resource_info_url: str) -> str:
        # if the link is not a share link from a lab, return the link, do not check compatibility
        if not ShareLink.is_lab_share_resource_link(resource_info_url):
            return resource_info_url

        self.message_dispatcher.notify_info_message(
            "Downloading the resource from a share link of another lab. Checking compatibility of the resource with the current lab")

        response = requests.get(resource_info_url, timeout=60)

        if response.status_code != 200:
            raise Exception("Error while getting information of the resource: " + response.text)
        shared_entity_info = ShareResourceInfoReponseDTO.from_json(response.c())

        # check if the resource is compatible with the current lab
        if not isinstance(shared_entity_info.entity_object, list):
            raise Exception("The resource is not compatible with the current lab")

        resources: List[dict] = shared_entity_info.entity_object

        # check if the resources are compatible with the current lab
        for resource in resources:
            TypingManager.check_typing_name_compatibility(resource['resource_typing_name'])

        # Zipping the resource
        self.message_dispatcher.notify_info_message("The resource is compatible with the lab.")

        return shared_entity_info.zip_entity_route

    def zip_and_download_resource_as_file(self, zip_resource_route: str) -> str:

        download_url = zip_resource_route
        if ShareLink.is_lab_share_resource_link(zip_resource_route):
            download_url = self.call_zip_resource(zip_resource_route)

        file_downloader = FileDownloader(Settings.get_instance().make_temp_dir(), self.message_dispatcher)

        # download the resource file
        return file_downloader.download_file(download_url)

    def call_zip_resource(self, url: str) -> str:
        """If the link is a share link from a lab, check the compatibility of the resource with the current lab,
        then zip the resource and return the download url
        """

        # Zipping the resource
        self.message_dispatcher.notify_info_message("The resource is compatible with the lab, zipping the resource")

        response = requests.post(url, timeout=60 * 30)

        if response.status_code != 200:
            raise Exception("Error while zipping the resource: " + response.text)

        zip_response = ShareResourceZippedResponseDTO.from_json(response.json())

        self.message_dispatcher.notify_info_message("Resource zipped, downloading the resource")
        return zip_response.download_entity_route

    def download_resource(self, download_url: str) -> str:
        """Download the resource from the share link
        """
        file_downloader = FileDownloader(Settings.get_instance().make_temp_dir(), self.message_dispatcher)

        # download the resource file
        return file_downloader.download_file(download_url)
