
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.note_template.note_template import NoteTemplate
from gws_core.note_template.task.note_template_param import NoteTemplateParam
from gws_core.note_template.task.note_template_resource import \
    NoteTemplateResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    unique_name="SelectNoteTemplate",
    short_description="Select a note template",
)
class SelectNoteTemplate(Task):
    """
    Task to select an existing note template and return a NoteTemplateResource to access the NoteTemplate.
    """

    input_specs: InputSpecs = InputSpecs()

    output_specs: OutputSpecs = OutputSpecs({
        'note_template': OutputSpec(NoteTemplateResource,
                                    human_name='Note template',
                                    short_description='Select a note template')
    })

    config_specs: ConfigSpecs = {
        'note_template': NoteTemplateParam(),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        note_template: NoteTemplate = params['note_template']
        return {
            'note_template': NoteTemplateResource(note_template_id=note_template.id)
        }
