# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from requests.models import Response

from gws_core.config.param.param_spec import StrParam
from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.service.external_lab_service import ExternalLabService
from gws_core.core.utils.settings import Settings
from gws_core.share.resource_downloader_base import ResourceDownloaderBase
from gws_core.share.share_link import ShareLinkType
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService

from ..config.config_params import ConfigParams
from ..config.config_types import ConfigSpecs


@task_decorator(unique_name="ResourceDownloaderHttp", human_name="Download resource from external source",
                short_description="Download a resource from an external source using a link")
class ResourceDownloaderHttp(ResourceDownloaderBase):
    """
    Task to download a resource from an external source using an HTTP link.

    If the link is from a Gencovery lab, the resource downloaded and imported in the correct type.
    Then it will be marked as received in the origin lab.

    If the link refers to a zip file, the zip file will be unzipped and the resource will be imported (File or Folder).

    If the link refers to a file, the file will be imported as a resource.

    """
    config_specs: ConfigSpecs = {'link': StrParam(
        human_name='Resource link', short_description='Link to download the resource')}

    config_name = 'link'
    link: str

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        self.link = params['link']

        file_downloader = FileDownloader(Settings.get_instance().make_temp_dir(), self.message_dispatcher)

        # download the resource file
        resource_file = file_downloader.download_file(self.link)

        return self.create_resource_from_file(resource_file)

    def run_after_task(self) -> None:
        """Save share info and mark the resource as received in lab
        """
        super().run_after_task()

        # check if the link is a share link from a lab
        if self.is_share_resource_link(self.link):
            self.log_info_message(
                "Marking the resource as received in the origin lab")
            # call the origin lab to mark the resource as received
            current_lab_info = ExternalLabService.get_current_lab_info(
                CurrentUserService.get_and_check_current_user())

            # retrieve the token which is the last part of the link
            share_token = self.link.split('/')[-1]
            response: Response = ExternalLabService.mark_shared_object_as_received(
                self.resource_loader.get_origin_info()['lab_api_url'],
                ShareLinkType.RESOURCE, share_token, current_lab_info)

            if response.status_code != 200:
                self.log_error_message(
                    "Error while marking the resource as received: " + response.text)

    @classmethod
    def is_share_resource_link(cls, link: str) -> bool:
        """Check if the link is a share resource link, it must start with https://glab,
        contains share/resource/download and end with a token
        """
        return link.startswith('https://glab') and link.find('share/resource/download/') != -1
