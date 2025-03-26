

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.note.note_dto import NoteSaveDTO
from gws_core.note.note_service import NoteService
from gws_core.note_template.note_template import NoteTemplate
from gws_core.note_template.task.note_template_param import NoteTemplateParam
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .lab_note_resource import LabNoteResource


@task_decorator(
    unique_name="CreateLabNote",
    short_description="Create a lab note",
    hide=True,
)
class CreateLabNote(Task):
    """
    Task to create a note. The note is directly create and accessible in the notes sections.
    The note is updatable and a NoteResource is returned by this task to access and modify the note.

    It is recommended to place this task at the end of a workflow to create a note with the results of the workflow.
    To assure the note is not created if the workflow fails.
    """

    input_specs: InputSpecs = InputSpecs()

    output_specs: OutputSpecs = OutputSpecs({
        'note': OutputSpec(LabNoteResource, human_name='Note', short_description='Note created')
    })

    config_specs = ConfigSpecs({
        'template': NoteTemplateParam(optional=True),
        'title': StrParam(human_name='Title', short_description='Title of the note', optional=True),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        template: NoteTemplate = params['template']
        title: str = params['title']

        if not title:
            if template:
                title = template.title
            else:
                title = 'New generated note'
        note_dto = NoteSaveDTO(title=title, template_id=template.id if template else None)

        note = NoteService.create(note_dto)

        self.log_info_message(f"Note '{note.title}' created")

        return {
            'note': LabNoteResource(note.id)
        }
