
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.note.note import Note
from gws_core.note.task.note_param import NoteParam
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .lab_note_resource import LabNoteResource


@task_decorator(
    unique_name="SelectNote",
    short_description="Select a note",
)
class SelectNote(Task):
    """
    Task to select an existing note and return a NoteResource to access and modify the note.
    """

    input_specs: InputSpecs = InputSpecs()

    output_specs: OutputSpecs = OutputSpecs({
        'note': OutputSpec(LabNoteResource, human_name='Note', short_description='Select a note')
    })

    config_specs = ConfigSpecs({
        'note': NoteParam(),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        note: Note = params['note']
        return {
            'note': LabNoteResource(note_id=note.id)
        }
