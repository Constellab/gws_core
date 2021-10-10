

import json

from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param_spec import StrParam
from ...impl.file.file import File
from ...impl.file.file_store import FileStore
from ...impl.file.local_file_store import LocalFileStore
from ...io.io_spec import InputSpecs, OutputSpecs
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="WriteToJsonFile", human_name="Write to file",
                short_description="Simple task to write a resource json data to a file in local store")
class WriteToJsonFile(Task):
    input_specs: InputSpecs = {'resource': Resource}
    output_specs: OutputSpecs = {'file': File}
    config_specs: ConfigSpecs = {'filename': StrParam(short_description='Name of the file')}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file_store: FileStore = LocalFileStore.get_default_instance()

        file: File = file_store.create_empty(params.get_value('filename') + '.json')

        resource: Resource = inputs['resource']
        file.write(json.dumps(resource.view_as_json().to_dict()))

        return {"file": file}
