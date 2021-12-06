

from typing import List

from gws_core import (ConfigParams, Task, TaskInputs, TaskOutputs,
                      transformer_decorator)
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param_spec import IntParam
from gws_core.experiment.experiment import Experiment
from gws_core.impl.robot.robot_resource import Robot
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.task.task_model import TaskModel
from gws_core.task.transformer.transformer import TransformerDict
from gws_core.task.transformer.transformer_service import TransformerService
from gws_core.test.base_test_case import BaseTestCase


@transformer_decorator('RobotTransform', resource_type=Robot)
class RobotTransform(Task):

    config_specs: ConfigSpecs = {'age': IntParam()}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        robot: Robot = inputs.get('resource')
        robot.age = params['age']
        return {'resource': robot}


class TestTaskTransformer(BaseTestCase):

    async def test_create_transformer_experiment(self):

        age_config = 99

        # create a robot resource
        robot = Robot.empty()
        self.assertNotEqual(robot.age, age_config)
        robot_model = ResourceModel.save_from_resource(robot, origin=ResourceOrigin.IMPORTED)

        # create and run
        transformers: List[TransformerDict] = [
            {'typing_name': RobotTransform._typing_name, 'config_values': {'age': age_config}}]
        experiment: Experiment = await TransformerService.create_and_run_transformer_experiment(transformers, robot_model.id)

        # retrieve robot and check age
        sink: TaskModel = experiment.protocol_model.get_process('sink')
        robot: Robot = sink.inputs.get_resource_model('resource').get_resource()
        self.assertEqual(robot.age, age_config)
