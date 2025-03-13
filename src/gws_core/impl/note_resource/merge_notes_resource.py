

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .note_resource import NoteResource


@task_decorator(
    unique_name="MergeNoteResources",
    human_name="Merge note resources",
    short_description="Merge multiple note resources into one",
)
class MergeNoteResources(Task):
    """
    Merge multiple note resource into a new note resource.
    """

    input_specs: InputSpecs = DynamicInputs({
        'source': InputSpec(NoteResource, human_name='Note resource')
    }, additionnal_port_spec=InputSpec(NoteResource, human_name='Note resource'))

    output_specs: OutputSpecs = OutputSpecs({
        'note': OutputSpec(NoteResource, human_name='Note resource')
    })

    config_specs: ConfigSpecs = {
        'title':
        StrParam(
            human_name='Title',
            short_description='Title of the new note resource, if empty the first note resource title is used',
            default_value=''), }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # prepare the input
        resource_list: ResourceList = inputs["source"]

        note_resource = NoteResource()

        index = 1
        for resource in resource_list:
            if not isinstance(resource, NoteResource):
                raise ValueError(f"Input {index} is not an note resource")

            if index == 1:
                note_resource.title = params['title'] or resource.title

            note_resource.append_note_resource(resource)
            index += 1

        return {
            'note': note_resource
        }
