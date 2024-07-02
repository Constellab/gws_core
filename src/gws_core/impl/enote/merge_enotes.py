

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

from .enote_resource import ENoteResource


@task_decorator(
    unique_name="MergeENotes",
    human_name="Merge e-notes",
    short_description="Merge multiple e-notes into one",
)
class MergeENotes(Task):
    """
    Append content to an existing e-note.
    """

    input_specs: InputSpecs = DynamicInputs({
        'source': InputSpec(ENoteResource, human_name='E-note')
    }, additionnal_port_spec=InputSpec(ENoteResource, human_name='E-note'))

    output_specs: OutputSpecs = OutputSpecs({
        'enote': OutputSpec(ENoteResource, human_name='E-note')
    })

    config_specs: ConfigSpecs = {
        'title': StrParam(human_name='Title', short_description='Title of the new e-note, if empty the first e-note title is used',
                          default_value=''),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # prepare the input
        resource_list: ResourceList = inputs["source"]

        enote_resource = ENoteResource()

        index = 1
        for resource in resource_list:
            if not isinstance(resource, ENoteResource):
                raise ValueError(f"Input {index} is not an e-note")

            if index == 1:
                enote_resource.title = params['title'] or resource.title

            enote_resource.append_enote(resource)
            index += 1

        return {
            'enote': enote_resource
        }
