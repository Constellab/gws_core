

import os

from gws_core.brick.technical_doc_service import TechnicalDocService
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.impl.file.file import File
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    unique_name="GenerateTechnicalDocMarkdown",
    short_description="Generate technical documentationof a brick as markdown",
)
class GenerateTechnicalDocMarkdown(Task):
    """
    Generate technical documentation of a brick as markdown.
    This task takes the brick name as input and an object type (Resource, Task, Protocol)
    and returns the technical documentation of the brick in markdown format.

    That markdown file can be use to train an AI model to learn about the brick functionalities.
    """

    output_specs: OutputSpecs = OutputSpecs({
        'markdown': OutputSpec(
            File,
            human_name='Markdown',
            short_description='The technical documentation of the brick in markdown format',
        )
    })

    config_specs: ConfigSpecs = {
        'brick_name': StrParam(human_name='Brick name',
                               short_description='The name of the brick to generate the technical documentation'),
        'object_type': StrParam(human_name='Object type',
                                short_description='The object type to generate the technical documentation',
                                allowed_values=['Resource', 'Task', 'Protocol']),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        result: str = None
        brick_name: str = params['brick_name']
        object_type: str = params['object_type']

        if object_type == 'Task':
            result = TechnicalDocService.generate_tasks_technical_doc_as_md(brick_name)
        elif object_type == 'Protocol':
            result = TechnicalDocService.generate_protocols_technical_doc_as_md(brick_name)
        elif object_type == 'Resource':
            result = TechnicalDocService.generate_resources_technical_doc_as_md(brick_name)

        file_name = f'{brick_name}_{object_type}_technical_doc.md'

        tmp_dir = self.create_tmp_dir()

        file_path = os.path.join(tmp_dir, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(result)

        return {
            'markdown': File(file_path)
        }
