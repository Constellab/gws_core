# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import List, Type

from requests.models import Response

from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.service.external_lab_service import (
    ExternalLabService, ExternalLabWithUserInfo)
from gws_core.core.utils.settings import Settings
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.resource.resource_zipper import ResourceUnzipper
from gws_core.share.share_link import ShareLinkType
from gws_core.share.shared_entity_info import (SharedEntityInfo,
                                               SharedEntityMode)
from gws_core.share.shared_resource import SharedResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_file_downloader import TaskFileDownloader
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


@task_decorator(unique_name="ImportResourceFromLab", human_name="Download resource from lab",
                short_description="Download a resource from an external lab")
class ResourceDownloader(Task):
    input_specs: InputSpecs = {}
    output_specs: OutputSpecs = {'resource': OutputSpec(Resource, human_name='Imported resource', sub_class=True)}
    config_specs: ConfigSpecs = {'link': StrParam(
        human_name='Resource link', short_description='Link to download the resource')}

    resource_unzipper: ResourceUnzipper
    link: str

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        self.link = params['link']

        file_downloader = TaskFileDownloader(ResourceDownloader.get_brick_name(), self.message_dispatcher)

        # create a temp dir
        temp_dir = Settings.get_instance().make_temp_dir()
        zip_file = os.path.join(temp_dir, 'resource.zip')

        # download the resource zip
        file_downloader.download_file(self.link, destination_path=zip_file)

        # Convert the zip file to a resource
        self.log_info_message("Unzipping the resource")
        self.resource_unzipper = ResourceUnzipper(zip_file)
        resource = self.resource_unzipper.load_resource()

        return {'resource': resource}

    def run_after_task(self) -> None:
        """Save share info and mark the resource as received in lab
        """
        if not self.resource_unzipper:
            self.log_error_message("The resource unzipper is not set, can mark resource as received")

        # Create the shared entity info
        self.log_info_message("Storing the resource origin info")
        resources: List[Resource] = self.resource_unzipper.get_all_generated_resources()
        for resource in resources:
            self._create_shared_entity(SharedResource, resource._model_id, SharedEntityMode.RECEIVED,
                                       self.resource_unzipper.get_origin_info(),
                                       CurrentUserService.get_and_check_current_user())

        self.log_info_message("Marking the resource as received in the origin lab")
        # call the origin lab to mark the resource as received
        current_lab_info = ExternalLabService.get_current_lab_info(CurrentUserService.get_and_check_current_user())

        # retrieve the token which is the last part of the link
        share_token = self.link.split('/')[-1]
        response: Response = ExternalLabService.mark_shared_object_as_received(
            self.resource_unzipper.get_origin_info()['lab_api_url'],
            ShareLinkType.RESOURCE, share_token, current_lab_info)

        if response.status_code != 200:
            self.log_error_message("Error while marking the resource as received: " + response.text)

        # clear temps files
        self.log_info_message("Cleaning the temp files")
        self.resource_unzipper.delete_temp_dir_and_files()

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
