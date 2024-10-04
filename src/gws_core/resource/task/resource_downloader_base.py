

from abc import abstractmethod
from typing import List, Literal

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.utils.compress.compress import Compress
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.resource.resource_loader import ResourceLoader
from gws_core.share.shared_dto import SharedEntityMode
from gws_core.share.shared_resource import SharedResource
from gws_core.task.task import Task
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


class ResourceDownloaderBase(Task):
    """
    Abstract class to aggregate common methods for resource downloader tasks

    """
    OUTPUT_NAME = 'resource'

    input_specs: InputSpecs = InputSpecs({})
    output_specs: OutputSpecs = OutputSpecs({'resource': OutputSpec(
        Resource, human_name='Imported resource', sub_class=True)})
    config_specs: ConfigSpecs = {}

    uncompressConfig = StrParam(human_name="Uncompress file", allowed_values=['auto', 'yes', 'no'],
                                default_value='auto',
                                short_description="Option to uncompress the file if it is compresses.")

    resource_loader: ResourceLoader = None

    @abstractmethod
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        pass

    def create_resource_from_file(
            self, resource_file: str, uncompress_option: Literal['auto', 'yes', 'no']) -> Resource:
        """Methode to create the resource from a file (once downloaded) and return it as a task output
        """

        # case of a file that is not a zip, we directly save it as a resource
        if not Compress.is_compressed_file(resource_file):
            if uncompress_option == 'yes':
                raise Exception("The file is not a compress file. Please disbale compress option.")
            self.log_info_message("Saving file as a resource")
            return File(resource_file)

        if uncompress_option == 'no':
            self.log_info_message("Saving compressed file")
            return File(resource_file)

        # Convert the zip file to a resource
        try:
            self.log_info_message("Uncompressing the file")
            self.resource_loader = ResourceLoader.from_compress_file(resource_file)
        except Exception as err:
            if uncompress_option == 'yes':
                raise Exception("Error while unzipping the file. Error: {err}.")

            # skip if the option is auto
            self.log_error_message(f"Error while unzipping the file. Saving the file without decompress. Error: {err}.")
            return File(resource_file)

        self.log_info_message("Loading the resource")
        resource = self.resource_loader.load_resource()

        # delete the compressed file
        FileHelper.delete_file(resource_file)

        return resource

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
            SharedResource.create_from_lab_info(resource.get_model_id(), SharedEntityMode.RECEIVED,
                                                self.resource_loader.get_origin_info(),
                                                CurrentUserService.get_and_check_current_user())
