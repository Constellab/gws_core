# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_types import ConfigParams
from gws_core.config.param.param_spec import StrParam
from gws_core.impl.robot.robot_resource import Robot
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set import ResourceSet
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="ResourceStacker", short_description="Stack a set of resource in a resource set",
                hide=False)
class ResourceStacker(Task):
    input_specs: InputSpecs = {
        "resource_1": InputSpec(Resource),
        "resource_2": InputSpec(Resource, is_skippable=True),
        "resource_3": InputSpec(Resource, is_skippable=True),
    }
    output_specs: OutputSpecs = {'resource_set': OutputSpec(ResourceSet)}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        resource_1 = inputs.get('resource_1')

        if resource_1 is None:
            raise Exception('The first input must be provided')
        resource_2 = inputs.get('resource_2')
        resource_3 = inputs.get('resource_3')

        resource_set: ResourceSet = ResourceSet()

        self.log_info_message('Adding resource 1')
        if isinstance(resource_1, ResourceSet):
            # prevent nesting resource sets
            for _, sub_resource in resource_1.get_resources().items():
                resource_set.add_resource(sub_resource, create_new_resource=False)
        else:
            resource_set.add_resource(resource_1, create_new_resource=False)

        if resource_2 is not None:
            self.log_info_message('Adding resource 2')
            if isinstance(resource_2, ResourceSet):
                # prevent nesting resource sets
                for _, sub_resource in resource_2.get_resources().items():
                    resource_set.add_resource(sub_resource, create_new_resource=False)
            else:
                resource_set.add_resource(resource_2, create_new_resource=False)

        if resource_3 is not None:
            self.log_info_message('Adding resource 3')
            if isinstance(resource_3, ResourceSet):
                # prevent nesting resource sets
                for _, sub_resource in resource_3.get_resources().items():
                    resource_set.add_resource(sub_resource, create_new_resource=False)
            else:
                resource_set.add_resource(resource_3, create_new_resource=False)

        return {'resource_set': resource_set}

@task_decorator(unique_name="ResourcePicker", short_description="Pick a resource from a resource set",
                hide=False)
class ResourcePicker(Task):
    input_specs: InputSpecs = {
        "resource_set": InputSpec(ResourceSet),
    }
    output_specs: OutputSpecs = {'resource': OutputSpec(Resource, sub_class=True, is_constant=True)}

    config_specs = {
        'resource_name': StrParam(human_name="Resource name", short_description="The name of the resource to pick")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        resource_set: ResourceSet = inputs.get('resource_set')
        resource_name = params['resource_name']
        resource = resource_set.get_resource(resource_name)
        return {'resource': resource}
