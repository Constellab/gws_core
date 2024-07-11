

from requests.models import Response

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.service.external_lab_service import ExternalLabService
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_downloader import ResourceDownloader
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.share.resource.resource_downloader_base import \
    ResourceDownloaderBase
from gws_core.share.share_link import ShareLink
from gws_core.share.shared_dto import ShareLinkType
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(unique_name="ResourceDownloaderHttp", human_name="Download resource from external source",
                short_description="Download a resource from an external source using a link",
                style=TypingStyle.material_icon("cloud_download"))
class ResourceDownloaderHttp(ResourceDownloaderBase):
    """
    Task to download a resource from an external source using an HTTP link.

    If the link is from a Gencovery lab, the resource downloaded and imported in the correct type.
    Then it will be marked as received in the origin lab.

    If the link refers to a zip file, the zip file will be unzipped and the resource will be imported (File or Folder).

    If the link refers to a file, the file will be imported as a resource.

    """
    config_specs: ConfigSpecs = {
        'link': StrParam(human_name='Resource link', short_description='Link to download the resource'),
        'uncompress': ResourceDownloaderBase.uncompressConfig
    }

    LINK_PARAM_NAME = 'link'
    UNCOMPRESS_PARAM_NAME = 'uncompress'

    link: str

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        self.link = params['link']

        resource_downloader = ResourceDownloader(self.message_dispatcher)

        zip_resource_link = resource_downloader.check_compatiblity(self.link)

        # download the resource file
        resource_file = resource_downloader.zip_and_download_resource_as_file(zip_resource_link)

        resource = self.create_resource_from_file(resource_file, params['uncompress'])

        if ShareLink.is_lab_share_resource_link(self.link):
            # set a special origin for the resource
            resource.__origin__ = ResourceOrigin.IMPORTED_FROM_LAB
        return {'resource': resource}

    def run_after_task(self) -> None:
        """Save share info and mark the resource as received in lab
        """
        super().run_after_task()

        # check if the link is a share link from a lab
        if self.is_old_share_resource_link(
                self.link) or ShareLink.is_lab_share_resource_link(
                self.link) and self.resource_loader:
            self.log_info_message(
                "Marking the resource as received in the origin lab")
            # call the origin lab to mark the resource as received
            current_lab_info = ExternalLabService.get_current_lab_info(
                CurrentUserService.get_and_check_current_user())

            # retrieve the token which is the last part of the link
            share_token = self.link.split('/')[-1]
            response: Response = ExternalLabService.mark_shared_object_as_received(
                self.resource_loader.get_origin_info().lab_api_url,
                ShareLinkType.RESOURCE, share_token, current_lab_info)

            if response.status_code != 200:
                self.log_error_message(
                    "Error while marking the resource as received: " + response.text)

    @classmethod
    def is_old_share_resource_link(cls, link: str) -> bool:
        """Check if the link is a share resource link, it must start with https://glab,
        contains share/resource/download and end with a token
        TODO to remove once all the labs are updated to v >= 0.6.1
        """
        return link.startswith('https://glab') and link.find('share/resource/download/') != -1
