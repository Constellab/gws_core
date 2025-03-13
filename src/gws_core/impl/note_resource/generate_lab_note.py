

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.note.task.lab_note_resource import LabNoteResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .note_resource import NoteResource


@task_decorator("GenerateLabNote", human_name="Generate lab note from note resource",
                short_description="Task to generate a lab note from an note resource")
class GenerateLabNote(Task):
    """
    Generate a note from a note resource. After generation, a lab note will be created and available
    in notes pages.

    This taks is useful as the end of a scenario to convert generate a report of the scenario.
    In this case a NoteResource can be passed though the scenario and at the end, a lab note can be generated.
    """

    input_specs: InputSpecs = InputSpecs({
        'note': InputSpec(NoteResource, human_name='Note resource')
    })

    output_specs: OutputSpecs = OutputSpecs({
        'note': OutputSpec(LabNoteResource, human_name='Note', short_description='New note')
    })

    config_specs: ConfigSpecs = {
        'title': StrParam(human_name='Note title', short_description='This overides the note resource title',
                          optional=True)
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        note_resource: NoteResource = inputs['note']

        note = note_resource.export_as_lab_note(params['title'], self.get_scenario_id())

        return {
            'note': LabNoteResource(note.id)
        }
