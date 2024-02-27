# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import StrParam
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .resource_set import ResourceSet


@task_decorator(unique_name="ResourceStacker", short_description="Stack a set of resource in a resource set",
                hide=False, icon="format_list_bulleted")
class ResourceStacker(Task):

    config_specs: ConfigSpecs = {'keys': ParamSet(
        {'key': StrParam(human_name="Resource key", short_description="The key of the resource to stack", optional=True)},
        optional=True
    )}
    input_specs: InputSpecs = DynamicInputs()
    output_specs: OutputSpecs = OutputSpecs({'resource_set': OutputSpec(ResourceSet)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        resource_list: ResourceList = inputs.get('source')

        configs: List[dict] = params.get_value('keys')

        resource_set: ResourceSet = ResourceSet()

        i = 0
        for resource in resource_list:
            if resource is not None:

                if isinstance(resource, ResourceSet):
                    # prevent nesting resource sets
                    self.log_info_message(f'Adding sub resource set for resource {str(i + 1)}')
                    for _, sub_resource in resource.get_resources().items():
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
                hide=False, icon="format_list_bulleted")
class ResourcePicker(Task):
    input_specs: InputSpecs = InputSpecs({
        "resource_set": InputSpec(ResourceSet),
    })
    output_specs: OutputSpecs = OutputSpecs({'resource': OutputSpec(Resource, sub_class=True, is_constant=True)})

    config_specs = {
        'resource_name': StrParam(human_name="Resource name", short_description="The name of the resource to pick")
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        resource_set: ResourceSet = inputs.get('resource_set')
        resource_name = params['resource_name']
        resource = resource_set.get_resource(resource_name)
        return {'resource': resource}
