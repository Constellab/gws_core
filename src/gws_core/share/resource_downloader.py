# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type

from requests.models import Response

from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.service.external_lab_service import (
    ExternalLabService, ExternalLabWithUserInfo)
from gws_core.core.utils.compress.compress import Compress
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.resource.resource_zipper import ResourceLoader
from gws_core.share.share_link import ShareLinkType
from gws_core.share.shared_entity_info import (SharedEntityInfo,
                                               SharedEntityMode)
from gws_core.share.shared_resource import SharedResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


@task_decorator(unique_name="ImportResourceFromLab", human_name="Download resource from source",
                short_description="Download a resource from an external source")
class ResourceDownloader(Task):
    """
    Task to download a resource from an external source.

    If the link is from a Gencovery lab, the resource downloaded and imported in the correct type.
    Then it will be marked as received in the origin lab.

    If the link refers to a zip file, the zip file will be unzipped and the resource will be imported (File or Folder).

    If the link refers to a file, the file will be imported as a resource.

    """
    input_specs: InputSpecs = {}
    output_specs: OutputSpecs = {'resource': OutputSpec(
        Resource, human_name='Imported resource', sub_class=True)}
    config_specs: ConfigSpecs = {'link': StrParam(
        human_name='Resource link', short_description='Link to download the resource')}

    config_name = 'link'

    resource_loader: ResourceLoader
    link: str

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        self.link = params['link']
        self.resource_loader = None

        file_downloader = FileDownloader(Settings.get_instance().make_temp_dir(), self.message_dispatcher)

        # download the resource file
        resource_file = file_downloader.download_file(self.link)

        # case of a file that is not a zip, we directly save it as a resource
        if not Compress.is_compressed_file(resource_file):
            self.log_info_message("Saving file as a resource")
            return {'resource': File(resource_file)}

        # Convert the zip file to a resource
        self.log_info_message("Unzipping the file")
        self.resource_loader = ResourceLoader.from_compress_file(resource_file)

        # is the uncompress folder is a resource export
        self.log_info_message("Loading the resource")
        resource = self.resource_loader.load_resource()
        return {'resource': resource}

    def run_after_task(self) -> None:
        """Save share info and mark the resource as received in lab
        """
        if not self.resource_loader:
            return

        # clear temps files
        self.log_info_message("Cleaning the temp files")
        self.resource_loader.delete_resource_folder()

        if not self.resource_loader.is_resource_zip():
            return

        # Create the shared entity info
        self.log_info_message("Storing the resource origin info")
        resources: List[Resource] = self.resource_loader.get_all_generated_resources()
        for resource in resources:
            self._create_shared_entity(SharedResource, resource._model_id, SharedEntityMode.RECEIVED,
                                       self.resource_loader.get_origin_info(),
                                       CurrentUserService.get_and_check_current_user())

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

    def _create_shared_entity(self, shared_entity_type: Type[SharedEntityInfo], entity_id: str,
                              mode: SharedEntityMode, lab_info: ExternalLabWithUserInfo, created_by: User) -> None:
        """Method that log the resource origin for each imported resources
        """

        shared_entity = shared_entity_type()
        shared_entity.entity = entity_id
        shared_entity.share_mode = mode
        shared_entity.lab_id = lab_info['lab_id']
        shared_entity.lab_name = lab_info['lab_name']
        shared_entity.user_id = lab_info['user_id']
        shared_entity.user_firstname = lab_info['user_firstname']
        shared_entity.user_lastname = lab_info['user_lastname']
        shared_entity.space_id = lab_info['space_id']
        shared_entity.space_name = lab_info['space_name']
        shared_entity.created_by = created_by
        shared_entity.save()

    @classmethod
    def is_share_resource_link(cls, link: str) -> bool:
        """Check if the link is a share resource link, it must start with https://glab,
        contains share/resource/download and end with a token
        """
        return link.startswith('https://glab') and link.find('share/resource/download/') != -1
