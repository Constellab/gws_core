# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import List, Type

from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.core.service.external_lab_service import ExternalLabWithUserInfo
from gws_core.core.utils.compress.compress import Compress
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.resource.resource_zipper import ResourceLoader
from gws_core.share.shared_entity_info import (SharedEntityInfo,
                                               SharedEntityMode)
from gws_core.share.shared_resource import SharedResource
from gws_core.task.task import Task
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


class ResourceDownloaderBase(Task):
    """
    Abstract class to aggregate common methods for resource downloader tasks

    """
    input_specs: InputSpecs = {}
    output_specs: OutputSpecs = {'resource': OutputSpec(
        Resource, human_name='Imported resource', sub_class=True)}
    config_specs: ConfigSpecs = {}

    resource_loader: ResourceLoader

    @abstractmethod
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        pass

    def create_resource_from_file(self, resource_file: str) -> TaskOutputs:
        """Methode to create the resource from a file (once downloaded) and return it as a task output
        """

        # case of a file that is not a zip, we directly save it as a resource
        if not Compress.is_compressed_file(resource_file):
            self.log_info_message("Saving file as a resource")
            return {'resource': File(resource_file)}

        # Convert the zip file to a resource
        self.log_info_message("Unzipping the file")
        self.resource_loader = ResourceLoader.from_compress_file(resource_file)

        self.log_info_message("Loading the resource")
        resource = self.resource_loader.load_resource()

        # delete the compressed file
        FileHelper.delete_file(resource_file)

        return {'resource': resource}

    def run_after_task(self) -> None:
        """Save share info, clean temp files, etc
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
