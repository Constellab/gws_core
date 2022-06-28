# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_types import ConfigParams
from gws_core.impl.robot.robot_resource import Robot
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set import ResourceSet
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="ResourceSetGenerator",
                hide=False)
class ResourceSetGenerator(Task):
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
        resource_set.add_resource(resource_1, create_new_resource=False)

        if resource_2 is not None:
            resource_set.add_resource(resource_2, create_new_resource=False)

        if resource_3 is not None:
            resource_set.add_resource(resource_3, create_new_resource=False)

        resource_set.add_resource(Robot.empty(), 'robot')

        return {'resource_set': resource_set}
