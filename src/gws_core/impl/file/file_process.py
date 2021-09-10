

import json

from ...config.config_params import ConfigParams
from ...config.config_spec import ConfigSpecs
from ...impl.file.file import File
from ...impl.file.file_store import FileStore
from ...impl.file.local_file_store import LocalFileStore
from ...io.io_spec import InputSpecs, OutputSpecs
from ...process.process import Process
from ...process.process_decorator import process_decorator
from ...process.process_io import ProcessInputs, ProcessOutputs
from ...resource.resource import Resource


@process_decorator(unique_name="WriteToJsonFile", human_name="Write to file",
                   short_description="Simple process to write a resource json data to a file in local store")
class WriteToJsonFile(Process):
    input_specs: InputSpecs = {'resource': Resource}
    output_specs: OutputSpecs = {'file': File}
    config_specs: ConfigSpecs = {'filename': {'type': str, 'description': 'Name of the file'}}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        file_store: FileStore = LocalFileStore.get_default_instance()

        file: File = file_store.create_empty(config.get_param('filename') + '.json')

        resource: Resource = inputs['resource']
        file.write(json.dumps(resource.to_json()))

        return {"file": file}
