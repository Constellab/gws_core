# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .resource_set import ResourceSet


@task_decorator(unique_name="ResourceStacker", short_description="Stack a set of resource in a resource set",
                hide=False)
class ResourceStacker(Task):

    config_specs: ConfigSpecs = {
        'resource_1_key': StrParam(optional=True, human_name='Key of resource 1 in the resource set'),
        'resource_2_key': StrParam(optional=True, human_name='Key of resource 2 in the resource set'),
        'resource_3_key': StrParam(optional=True, human_name='Key of resource 3 in the resource set'),
        'resource_4_key': StrParam(optional=True, human_name='Key of resource 4 in the resource set'),
        'resource_5_key': StrParam(optional=True, human_name='Key of resource 5 in the resource set'),
    }
    input_specs: InputSpecs = InputSpecs({
        "resource_1": InputSpec(Resource),
        "resource_2": InputSpec(Resource, is_optional=True),
        "resource_3": InputSpec(Resource, is_optional=True),
        "resource_4": InputSpec(Resource, is_optional=True),
        "resource_5": InputSpec(Resource, is_optional=True),
    })
    output_specs: OutputSpecs = OutputSpecs({'resource_set': OutputSpec(ResourceSet)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        resource_1 = inputs.get('resource_1')

        if resource_1 is None:
            raise Exception('The first input must be provided')

        resources: List[Resource] = [
            resource_1, inputs.get('resource_2'),
            inputs.get('resource_3'),
            inputs.get('resource_4'),
            inputs.get('resource_5')]
        configs: List[str] = [params.get('resource_1_key'), params.get('resource_2_key'), params.get(
            'resource_3_key'), params.get('resource_4_key'), params.get('resource_5_key')]

        resource_set: ResourceSet = ResourceSet()

        i = 0
        for resource in resources:
            if resource is not None:

                if isinstance(resource, ResourceSet):
                    # prevent nesting resource sets
                    self.log_info_message(f'Adding sub resource set for resource {str(i + 1)}')
                    for _, sub_resource in resource.get_resources().items():
                        resource_set.add_resource(sub_resource, create_new_resource=False)
                else:
                    resource_key = configs[i] if configs[i] is not None else resource.name
                    self.log_info_message(f"Adding resource {str(i + 1)} with key '{resource_key}'")
                    resource_set.add_resource(resource, resource_key, create_new_resource=False)
            i += 1

        return {'resource_set': resource_set}


@task_decorator(unique_name="ResourcePicker", short_description="Pick a resource from a resource set",
                hide=False)
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
