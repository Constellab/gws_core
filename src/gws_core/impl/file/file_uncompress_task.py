

from gws_core.core.utils.compress.compress import Compress
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource_loader import ResourceLoader

from ...config.config_params import ConfigParams
from ...impl.file.file import File
from ...io.io_specs import InputSpecs, OutputSpecs
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="FileUncompressTask", human_name="Uncompress file",
                short_description="Uncompress a file")
class FileUncompressTask(Task):

    input_specs = InputSpecs({"compressed_file": InputSpec(File)})
    output_specs = OutputSpecs({'resource': OutputSpec(
        Resource, human_name='Imported resource', sub_class=True)})

    resource_loader: ResourceLoader = None

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file: File = inputs['compressed_file']

        # case of a file that is not a zip, we directly save it as a resource
        if not Compress.is_compressed_file(file.path):
            raise Exception('The provided file is not a compressed file or is not supported')

        # Convert the zip file to a resource
        self.log_info_message("Uncompressing the file")
        self.resource_loader = ResourceLoader.from_compress_file(file.path)

        self.log_info_message("Loading the resource")
        resource = self.resource_loader.load_resource()

        return {'resource': resource}

    def run_after_task(self) -> None:
        """Save share info, clean temp files, etc
        """
        if not self.resource_loader:
            return

        # clear temps files
        self.log_info_message("Cleaning the temp files")
        self.resource_loader.delete_resource_folder()
