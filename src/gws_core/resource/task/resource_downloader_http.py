from typing import Literal

from requests.models import Response

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.service.front_service import FrontService
from gws_core.core.utils.utils import Utils
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_downloader import (
    LabShareResourceDownloader,
    ResourceDownloader,
)
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.task.resource_downloader_base import ResourceDownloaderBase
from gws_core.share.share_link import ShareLink
from gws_core.share.shared_dto import (
    ShareEntityCreateMode,
    ShareLinkEntityType,
)
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService

ResourceDownloaderCreateOption = Literal["Skip if exists", "Force new resource"]


@task_decorator(
    unique_name="ResourceDownloaderHttp",
    human_name="Download resource from external source",
    short_description="Download a resource from an external source using a link",
    style=TypingStyle.material_icon("cloud_download"),
)
class ResourceDownloaderHttp(ResourceDownloaderBase):
    """
    Task to download a resource from an external source using an HTTP link.

    If the link is from a Gencovery lab, the resource downloaded and imported in the correct type.
    Then it will be marked as received in the origin lab.
    In this case an automatic scenario might be created in the source lab to zip the resource before sharing it.

    If the link refers to a zip file, the zip file will be unzipped and the resource will be imported (File or Folder).

    If the link refers to a file, the file will be imported as a resource.
    """

    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "link": StrParam(
                human_name="Resource link", short_description="Link to download the resource"
            ),
            "uncompress": ResourceDownloaderBase.uncompress_config,
            "create_option": StrParam(
                human_name="Create option",
                allowed_values=Utils.get_literal_values(ResourceDownloaderCreateOption),
                default_value="Skip if exists",
            ),
        }
    )

    LINK_PARAM_NAME = "link"

    link: str

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        self.link = params["link"]

        # Use factory to create the appropriate downloader
        resource_downloader = ResourceDownloader.create(self.link, self.message_dispatcher)

        create_option = params["create_option"]
        uncompressed_option = params["uncompress"]

        resource_loader_mode: ShareEntityCreateMode
        # We keep the id only if option activated and uncompressed option is activated as well
        if create_option == "Skip if exists" and uncompressed_option != "no":
            resource_loader_mode = ShareEntityCreateMode.KEEP_ID
        else:
            resource_loader_mode = ShareEntityCreateMode.NEW_ID

        # if we keep the resource id and it's a lab share link, check if the resource already exists
        if resource_loader_mode == ShareEntityCreateMode.KEEP_ID and isinstance(
            resource_downloader, LabShareResourceDownloader
        ):
            self._check_existing_resource(resource_downloader)

        # download the resource file
        resource_file = resource_downloader.download()

        # set the origin to imported from lab if the link is from a lab share link
        resource_origin = (
            ResourceOrigin.IMPORTED_FROM_LAB
            if isinstance(resource_downloader, LabShareResourceDownloader)
            else None
        )

        resource = self.create_resource_from_file(
            resource_file, uncompressed_option, resource_loader_mode, resource_origin
        )

        return {"resource": resource}

    def run_after_task(self) -> None:
        """Save share info and mark the resource as received in lab"""
        super().run_after_task()

        # check if the link is a share link from a lab
        if ShareLink.is_lab_share_resource_link(self.link) and self.resource_loader:
            self.log_info_message("Marking the resource as received in the origin lab")
            # call the origin lab to mark the resource as received
            current_lab_info = ExternalLabApiService.get_current_lab_info(
                CurrentUserService.get_and_check_current_user()
            )

            # retrieve the token which is the last part of the link
            share_token = self.link.split("/")[-1]
            response: Response = ExternalLabApiService.mark_shared_object_as_received(
                self.resource_loader.get_origin_info().lab_api_url,
                ShareLinkEntityType.RESOURCE,
                share_token,
                current_lab_info,
            )

            if response.status_code != 200:
                self.log_error_message(
                    "Error while marking the resource as received: " + response.text
                )

    def _check_existing_resource(
        self, share_resource_downloader: LabShareResourceDownloader
    ) -> None:
        """Check if the resource already exists in the current lab.

        :param resource_downloader: The resource downloader
        :return: ResourceModel if it exists, None otherwise
        """
        for resource_dto in share_resource_downloader.get_resources_info():
            resource_model = ResourceModel.get_by_id(resource_dto.id)
            if resource_model:
                if share_resource_downloader.is_main_resource(resource_model.id):
                    raise Exception(
                        "The resource '"
                        + resource_dto.name
                        + "' already exists in the current lab."
                        + f' <a href="{FrontService.get_resource_url(resource_model.id)}">Click here to view the existing resource</a>.'
                    )
                else:
                    raise Exception(
                        "The child resource '"
                        + resource_dto.name
                        + "' of the main resource already exists in the current lab. Please use the 'Force new resource' option to create a new copy of the resource."
                        + f' <a href="{FrontService.get_resource_url(resource_model.id)}">Click here to view the existing resource</a>.'
                    )

    @classmethod
    def build_config(
        cls,
        link: str,
        uncompress: Literal["auto", "yes", "no"],
        create_option: ResourceDownloaderCreateOption,
    ) -> ConfigParams:
        return ConfigParams(
            {cls.LINK_PARAM_NAME: link, "uncompress": uncompress, "create_option": create_option}
        )
