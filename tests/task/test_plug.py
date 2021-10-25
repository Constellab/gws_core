

from gws_core import Source, TaskTester
from gws_core.impl.robot.robot_resource import Robot
from gws_core.resource.resource_model import ResourceModel
from gws_core.task.task_io import TaskOutputs
from gws_core.test.base_test_case import BaseTestCase


class TestPlug(BaseTestCase):

    async def test_source(self):
        """Test the source task
        """
        robot: Robot = Robot.empty()
        robot_model: ResourceModel = ResourceModel.from_resource(robot)
        robot_model.save()

        task_tester = TaskTester(Source, {'resource_uri': robot_model.uri, 'resource_typing_name': Robot._typing_name})

        outputs: TaskOutputs = await task_tester.run()

        robot_o: Robot = outputs['resource']
        self.assertEqual(robot_o._model_uri, robot_model.uri)
