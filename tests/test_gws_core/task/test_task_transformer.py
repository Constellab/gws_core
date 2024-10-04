

from typing import List

from gws_core import ConfigParams, transformer_decorator
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import IntParam
from gws_core.impl.robot.robot_resource import Robot
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.task.transformer.transformer import Transformer
from gws_core.task.transformer.transformer_service import TransformerService
from gws_core.task.transformer.transformer_type import TransformerDict
from gws_core.test.base_test_case import BaseTestCase


@transformer_decorator('RobotTransform', resource_type=Robot)
class RobotTransform(Transformer):

    config_specs: ConfigSpecs = {'age': IntParam()}

    def transform(self, source: Robot, params: ConfigParams) -> Robot:
        source.age = params['age']
        return source


class TestTaskTransformer(BaseTestCase):

    def test_create_transformer_scenario(self):

        age_config = 99

        # create a robot resource
        robot = Robot.empty()
        self.assertNotEqual(robot.age, age_config)
        robot_model = ResourceModel.save_from_resource(robot, origin=ResourceOrigin.UPLOADED)

        # create and run
        transformers: List[TransformerDict] = [
            {'typing_name': RobotTransform.get_typing_name(), 'config_values': {'age': age_config}}]
        resource_model: ResourceModel = TransformerService.create_and_run_transformer_scenario(
            transformers, robot_model.id)

        self.assertEqual(resource_model.origin, ResourceOrigin.GENERATED)

        # retrieve robot and check age
        robot: Robot = resource_model.get_resource()
        self.assertEqual(robot.age, age_config)

    def test_call_transformers(self):

        age_config = 99

        transformers: List[TransformerDict] = [{
            'typing_name': RobotTransform.get_typing_name(),
            'config_values': {'age': 5}
        },
            {
            'typing_name': RobotTransform.get_typing_name(),
            'config_values': {'age': age_config}
        }]

        # create a robot resource
        robot = Robot.empty()
        new_robot: Robot = TransformerService.call_transformers(robot, transformers)

        self.assertEqual(new_robot.age, age_config)
