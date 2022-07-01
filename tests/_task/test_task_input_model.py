
from typing import List

from gws_core.experiment.experiment_interface import IExperiment
from gws_core.impl.robot.robot_protocol import (CreateSimpleRobot,
                                                MoveSimpleRobot)
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol import Protocol
from gws_core.protocol.protocol_decorator import protocol_decorator
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_spec import ProcessSpec
from gws_core.task.plug import Sink
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel
from gws_core.test.base_test_case import BaseTestCase


@protocol_decorator("RobotSuperTravelProto")
class RobotSuperTravelProto(Protocol):
    def configure_protocol(self) -> None:

        move: ProcessSpec = self.add_process(RobotMove, "move")

        self.add_interface('robot', move, 'robot')
        self.add_outerface('robot', move, 'robot')


@protocol_decorator("RobotMainTravel", )
class RobotMainTravel(Protocol):

    def configure_protocol(self) -> None:

        facto: ProcessSpec = self.add_process(RobotCreate, "facto")
        sub_travel: ProcessSpec = self.add_process(RobotSuperTravelProto, "sub_travel")

        # define the protocol output
        sink: ProcessSpec = self.add_process(Sink, 'sink')

        self.add_connectors([
            (facto >> 'robot', sub_travel << 'robot'),
            (sub_travel >> 'robot', sink << 'resource'),
        ])


class TestTaskInputModel(BaseTestCase):

    async def test_task_input_model(self):
        experiment: IExperiment = IExperiment(RobotMainTravel)
        await experiment.run()

        ################################ CHECK TASK INPUT ################################
        # Check if the Input resource was set
        sink: ProcessModel = experiment._experiment.protocol_model.get_process('sink')
        task_inputs: List[TaskInputModel] = list(
            TaskInputModel.get_by_resource_model(sink.inputs.get_resource_model('resource').id))
        self.assertEqual(len(task_inputs), 1)
        self.assertEqual(task_inputs[0].is_interface, False)
        self.assertEqual(task_inputs[0].port_name, "resource")

        # Check the TaskInput with a sub process and a resource that is an interface
        sub_travel: ProtocolModel = experiment._experiment.protocol_model.get_process('sub_travel')
        sub_move: TaskModel = sub_travel.get_process('move')
        task_inputs = list(TaskInputModel.get_by_task_model(sub_move.id))
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

        # Create another experiment that use the previous resource
        experiment_3: IExperiment = IExperiment(MoveSimpleRobot)
        experiment_3.get_protocol().get_process('source').set_param('resource_id', task_input.resource_model.id)
        await experiment_3.run()
        # Get all the task input where the resource is used in another experiment
        task_input: TaskInputModel = TaskInputModel.get_other_experiments(
            [task_input.resource_model.id], experiment_1._experiment.id).first()
        self.assertEqual(task_input.experiment.id, experiment_3._experiment.id)

        # Test deleting by experiment
        TaskInputModel.delete_by_experiment(experiment_1._experiment.id)
        self.assertEqual(TaskInputModel.get_by_experiment(experiment_1._experiment.id).count(), 0)
