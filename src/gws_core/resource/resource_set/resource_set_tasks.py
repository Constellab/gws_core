

from typing import List

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import StrParam
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .resource_set import ResourceSet


@task_decorator(unique_name="ResourceStacker", short_description="Stack a set of resource in a resource set",
                hide=False,
                style=TypingStyle.material_icon("format_list_bulleted", background_color="#FEC7B4"))
class ResourceStacker(Task):
    """
    Stack a set of resource in a resource set.
    This is useful when a task uses a resource set as input.

    The provided input resource are directly added to the output resource set (resource are not copied).

    If an input resource is a ResourceList or a ResourceSet, the resource are flatten and added to the output resource set.
    """

    config_specs = ConfigSpecs({'keys': ParamSet(ConfigSpecs(
        {'key': StrParam(human_name="Resource key", short_description="The key of the resource to stack", optional=True)}),
        optional=True, human_name="Resource keys", short_description="The keys of the resources to stack"
    )})
    input_specs: InputSpecs = DynamicInputs()
    output_specs: OutputSpecs = OutputSpecs({'resource_set': OutputSpec(ResourceSet)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        resource_list: ResourceList = inputs.get('source')

        configs: List[dict] = params.get_value('keys')

        resource_set: ResourceSet = ResourceSet()

        i = 0
        for resource in resource_list:
            if resource is not None:

                if isinstance(resource, ResourceListBase):
                    # prevent nesting resource sets
                    self.log_info_message(
                        f'Flatten sub resource for resource {str(i + 1)} because it is a resource list or set')
                    for sub_resource in resource.get_resources_as_set():
                        resource_set.add_resource(sub_resource, create_new_resource=False)
                else:
                    resource_key = configs[i]['key'] if len(
                        configs) > i and configs[i] and configs[i]['key'] else resource.name
                    self.log_info_message(f"Adding resource {str(i + 1)} with key '{resource_key}'")
                    resource_set.add_resource(resource, resource_key, create_new_resource=False)
            i += 1

        if len(resource_set) == 0:
            raise Exception("No resource found in the input")

        return {'resource_set': resource_set}


@task_decorator(unique_name="ResourcePicker", short_description="Pick a resource from a resource set",
                hide=False,
                style=TypingStyle.material_icon("format_list_bulleted", background_color="#FEC7B4"))
class ResourcePicker(Task):
    """
    Pick a resource from a resource set.

    This is useful when you need to extract a resource from a resource set to use it in another

    The picked resource references the original resource in the resource set and is not a copy.

    """
    input_specs: InputSpecs = InputSpecs({
        "resource_set": InputSpec(ResourceSet),
    })
    output_specs: OutputSpecs = DynamicOutputs(
        additionnal_port_spec=OutputSpec(Resource, sub_class=True, is_constant=True))

    config_specs = ConfigSpecs({'keys': ParamSet(ConfigSpecs(
        {'key': StrParam(human_name="Resource key", short_description="The key of the resource to pick")}),
        optional=False, human_name="Resource keys", short_description="The keys of the resources to pick"
    )})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        resource_set: ResourceSet = inputs.get('resource_set')
        configs: List[dict] = params.get_value('keys')

        resource_list = ResourceList()

        for config in configs:
            if config.get('key'):
                resource = resource_set.get_resource(config['key'])
                resource_list.add_resource(resource)

        return {'target': resource_list}
