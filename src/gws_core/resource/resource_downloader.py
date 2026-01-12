import requests

from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.utils.settings import Settings
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.resource_dto import ResourceModelDTO
from gws_core.share.share_link import ShareLink
from gws_core.share.shared_dto import ShareResourceInfoReponseDTO, ShareResourceZippedResponseDTO


class ResourceDownloader:
    """
    Base class to download a resource from different sources.

    Use the factory method `create()` to instantiate the appropriate downloader based on URL type.
    """

    message_dispatcher: MessageDispatcher

    def __init__(self, message_dispatcher: MessageDispatcher | None = None) -> None:
        if message_dispatcher is None:
            self.message_dispatcher = MessageDispatcher()
        else:
            self.message_dispatcher = message_dispatcher

    @staticmethod
    def create(
        url: str, message_dispatcher: MessageDispatcher | None = None
    ) -> "ResourceDownloader":
        """
        Factory method that creates the appropriate downloader based on URL type.

        :param url: The URL to download from
        :param message_dispatcher: Optional message dispatcher for notifications
        :return: LabShareResourceDownloader for lab share links, DirectUrlResourceDownloader otherwise
        """
        if ShareLink.is_lab_share_resource_link(url):
            return LabShareResourceDownloader(url, message_dispatcher)
        else:
            return DirectUrlResourceDownloader(url, message_dispatcher)

    def download(self) -> str:
        """
        Download the resource and return the path to the downloaded file.

        Must be implemented by subclasses.

        :return: Path to the downloaded file
        """
        raise NotImplementedError("Subclasses must implement download()")


class LabShareResourceDownloader(ResourceDownloader):
    """
    Downloader for lab share links with compatibility checking and resource info caching.
    """

    resource_info_url: str
    _shared_entity_info: ShareResourceInfoReponseDTO | None = None

    def __init__(
        self, resource_info_url: str, message_dispatcher: MessageDispatcher | None = None
    ) -> None:
        super().__init__(message_dispatcher)
        if not ShareLink.is_lab_share_resource_link(resource_info_url):
            raise ValueError("The provided URL is not a valid lab share resource link.")
        self.resource_info_url = resource_info_url

    def check_compatibility(self) -> str:
        """
        Check if the resource is compatible with the current lab.

        :return: The zip entity route URL
        """
        shared_entity_info = self._get_shared_entity_info()

        resources = shared_entity_info.entity_object

        # check if the resources are compatible with the current lab
        for resource in resources:
            TypingManager.check_typing_name_compatibility(resource.resource_typing_name)

        self.message_dispatcher.notify_info_message("The resource is compatible with the lab.")

        return shared_entity_info.zip_entity_route

    def is_main_resource(self, resource_model_id: str) -> bool:
        """
        Check if the given resource model ID corresponds to the main resource.

        :param resource_model_id: The resource model ID to check
        :return: True if it is the main resource, False otherwise
        """
        shared_entity_info = self._get_shared_entity_info()
        return shared_entity_info.entity_id == resource_model_id

    def get_resources_info(self) -> list[ResourceModelDTO]:
        """
        Get the list of ResourceModelDTOs from the shared entity info.

        :return: List of ResourceModelDTOs
        """
        shared_entity_info = self._get_shared_entity_info()
        return shared_entity_info.entity_object

    def download(self) -> str:
        """
        Check compatibility, zip the resource, and download it.

        :return: Path to the downloaded file
        """
        zip_route = self.check_compatibility()
        # Delegate to LabShareZipRouteDownloader for the zip + download part
        zip_downloader = LabShareZipRouteDownloader(zip_route, self.message_dispatcher)
        return zip_downloader.download()

    def _get_shared_entity_info(self) -> ShareResourceInfoReponseDTO:
        """
        Get and cache the shared entity info from the resource info URL.

        :return: The shared entity info
        """
        if self._shared_entity_info is not None:
            return self._shared_entity_info

        self.message_dispatcher.notify_info_message(
            "Downloading the resource from a share link of another lab. Checking compatibility of the resource with the current lab"
        )

        response = requests.get(self.resource_info_url, timeout=60)

        if response.status_code != 200:
            raise Exception("Error while getting information of the resource: " + response.text)
        shared_entity_info = ShareResourceInfoReponseDTO.from_json(response.json())

        # check if the resource is compatible with the current lab
        if not isinstance(shared_entity_info.entity_object, list):
            raise Exception("The resource is not compatible with the current lab")

        self._shared_entity_info = shared_entity_info

        return shared_entity_info


class LabShareZipRouteDownloader(ResourceDownloader):
    """
    Downloader for lab share zip route URLs (skips compatibility checking).
    Use when you already have the zip entity route URL, not the resource info URL.
    """

    zip_route_url: str

    def __init__(
        self, zip_route_url: str, message_dispatcher: MessageDispatcher | None = None
    ) -> None:
        super().__init__(message_dispatcher)
        if not ShareLink.is_lab_share_resource_link(zip_route_url):
            raise ValueError("The provided URL is not a valid lab share resource link.")
        self.zip_route_url = zip_route_url

    def download(self) -> str:
        """
        Zip the resource and download it (skips compatibility checking).

        :return: Path to the downloaded file
        """
        download_url = self._call_zip_resource(self.zip_route_url)
        # Delegate the actual download to DirectUrlResourceDownloader
        direct_downloader = DirectUrlResourceDownloader(download_url, self.message_dispatcher)
        return direct_downloader.download()

    def _call_zip_resource(self, url: str) -> str:
        """
        Call the lab API to zip the resource and return the download URL.

        :param url: The zip entity route URL
        :return: The download URL for the zipped resource
        """
        self.message_dispatcher.notify_info_message("Zipping the resource")

        response = requests.post(url, timeout=60 * 30)

        if response.status_code != 200:
            raise Exception("Error while zipping the resource: " + response.text)

        zip_response = ShareResourceZippedResponseDTO.from_json(response.json())

        self.message_dispatcher.notify_info_message("Resource zipped, downloading the resource")
        return zip_response.download_entity_route


class DirectUrlResourceDownloader(ResourceDownloader):
    """
    Downloader for direct HTTP/HTTPS URLs without compatibility checking.
    """

    download_url: str

    def __init__(
        self, download_url: str, message_dispatcher: MessageDispatcher | None = None
    ) -> None:
        super().__init__(message_dispatcher)
        self.download_url = download_url

    def download(self) -> str:
        """
        Download the resource directly from the URL.

        :return: Path to the downloaded file
        """
        file_downloader = FileDownloader(
            Settings.get_instance().make_temp_dir(), self.message_dispatcher
        )
        return file_downloader.download_file(self.download_url)
