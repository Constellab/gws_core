# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (ConfigParams, OutputSpecs, Task, TaskInputs, TaskOutputs,
                      task_decorator)
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.impl.robot.robot_resource import Robot
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set import ResourceSet
from gws_core.test.base_test_case import BaseTestCase


@task_decorator(unique_name="RobotsGenerator")
class RobotsGenerator(Task):

    output_specs: OutputSpecs = {'set': ResourceSet}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        robot_1 = Robot.empty()
        robot_1.age = 98
        robot_2 = Robot.empty()
        robot_2.age = 99

        resource_set: ResourceSet = ResourceSet()
        resource_set.add_resource(robot_1)
        resource_set.add_resource(robot_2)
        return {'set': resource_set}


class TestResourceSet(BaseTestCase):

    async def test_resource_set(self):

        resource_count = ResourceModel.select().count()
        experiment: IExperiment = IExperiment()
        robot_generator = experiment.get_protocol().add_process(RobotsGenerator, 'generator')

        await experiment.run()

        # check that it created 3 resource (1 for the resrouce set and 2 robots)
        self.assertEqual(ResourceModel.select().count(), resource_count + 3)

        resource_set: ResourceSet = robot_generator.get_output('set')

        self.assertEqual(len(resource_set.resources), 2)

        age = 0
        for resource in resource_set.resources:
            self.assertIsInstance(resource, Robot)
            age += resource.age

        # check the age, this will mean the two where correctly saved separatly
        self.assertEqual(age, 98 + 99)

        # test the view, reload the resource to simulate real view
        resource_set = ResourceModel.get_by_id_and_check(resource_set._model_id).get_resource()

        self.assertEqual(len(resource_set.view_resources_list({}).to_dict({})['data']), 2)

        experiment.reset()
        # check that the reset cleared the correct resources
        self.assertEqual(ResourceModel.select().count(), resource_count)
