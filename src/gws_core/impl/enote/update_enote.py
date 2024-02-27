# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_param import RichTextParam
from gws_core.impl.rich_text.rich_text_types import \
    RichTextParagraphHeaderLevel
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .enote_resource import ENoteResource


@task_decorator(
    unique_name="UpdatENote",
    human_name="Update e-note",
    short_description="Append content to an existing e-note",
)
class UpdatENote(Task):
    """
    Append content to an existing e-note.
    """

    input_specs: InputSpecs = InputSpecs({
        'enote': InputSpec(ENoteResource, human_name='E-note')
    })

    output_specs: OutputSpecs = OutputSpecs({
        'enote': OutputSpec(ENoteResource, human_name='E-note')
    })

    config_specs: ConfigSpecs = {
        'section-title': StrParam(optional=True, human_name='Section title',
                                  short_description='Title of the new section'),
        'enote': RichTextParam(human_name='E-note', short_description='Content to append to the input e-note')
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        enote_resource: ENoteResource = inputs['enote']
        section_title: str = params['section-title']
        enote_param: RichText = params['enote']

        if section_title is not None:
            enote_resource.add_header(section_title, RichTextParagraphHeaderLevel.HEADER_1)

        enote_resource.append_rich_text(enote_param)

        return {
            'enote': enote_resource
        }
