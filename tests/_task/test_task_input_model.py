
from typing import List

from gws_core.experiment.experiment_interface import IExperiment
from gws_core.impl.robot.robot_protocol import (CreateSimpleRobot,
                                                RobotWorldTravelProto)
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel
from gws_core.test.base_test_case import BaseTestCase


class TestTaskInputModel(BaseTestCase):

    async def test_task_input_model(self):
        experiment: IExperiment = IExperiment(RobotWorldTravelProto)
        await experiment.run()

        ################################ CHECK TASK INPUT ################################
        # Check if the Input resource was set
        fly_1: ProcessModel = experiment._experiment.protocol_model.get_process('fly_1')
        task_inputs: List[TaskInputModel] = list(
            TaskInputModel.get_by_resource_model(fly_1.inputs.get_resource_model('robot').id))
        self.assertEqual(len(task_inputs), 1)
        self.assertEqual(task_inputs[0].is_interface, False)
        self.assertEqual(task_inputs[0].port_name, "robot")

        # Check the TaskInput with a sub process and a resource that is an interface
        super_travel: ProtocolModel = experiment._experiment.protocol_model.get_process('super_travel')
        sub_move_4: TaskModel = super_travel.get_process('move_4')
        task_inputs = list(TaskInputModel.get_by_task_model(sub_move_4.id))
        self.assertEqual(len(task_inputs), 1)
        self.assertEqual(task_inputs[0].is_interface, True)

    async def test_task_input_model_select(self):
        # Test the select of input model task and delete by experiment
        experiment_1: IExperiment = IExperiment(CreateSimpleRobot)
        await experiment_1.run()

        experiment_2: IExperiment = IExperiment(CreateSimpleRobot)
        await experiment_2.run()

        task_input: TaskInputModel = TaskInputModel.get_by_experiment(experiment_1._experiment.id).first()
        self.assertIsNotNone(task_input)
        self.assertEqual(TaskInputModel.get_by_experiment(experiment_1._experiment.id).count(), 1)
        self.assertEqual(TaskInputModel.get_by_resource_model(task_input.resource_model.id).count(), 1)
        self.assertEqual(TaskInputModel.get_by_task_model(task_input.task_model.id).count(), 1)

        TaskInputModel.delete_by_experiment(experiment_1._experiment.id)
        self.assertEqual(TaskInputModel.get_by_experiment(experiment_1._experiment.id).count(), 0)
