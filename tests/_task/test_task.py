# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod

from gws_core import (BaseTestCase, ConfigParams, Experiment,
                      ExperimentService, GTest, ProcessFactory, ProtocolModel,
                      ProtocolService, ResourceModel, Robot, RobotCreate, Task,
                      TaskInputs, TaskModel, TaskOutputs, task_decorator)
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_run_service import ExperimentRunService
from tests.protocol_examples import TestSimpleProtocol


@task_decorator(unique_name="RunAfterTask")
class RunAfterTask(Task):
    @abstractmethod
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return None

    def run_task(self) -> None:
        raise Exception('run_after_task')


class TestTask(BaseTestCase):

    def test_task_singleton(self):

        p0: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=RobotCreate)
        p1: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=RobotCreate)
        # p0.title = "First 'Create' task"
        # p0.description = "This is the description of the task"
        p0.save_full()

        self.assertTrue(p0.id != p1.id)

    def test_process(self):

        proto: ProtocolModel = ProtocolService.create_protocol_model_from_type(TestSimpleProtocol)

        p0: TaskModel = proto.get_process('p0')
        p1: TaskModel = proto.get_process('p1')
        p2: TaskModel = proto.get_process('p2')

        self.assertTrue(p0.created_by.is_sysuser)
        self.assertEqual(proto.created_by, GTest.user)

        self.assertEqual(len(p1.outputs.get_next_procs()), 1)
        self.assertEqual(len(p2.outputs.get_next_procs()), 2)

        p2.config.set_value('food_weight', '5.6')

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=proto)

        self.assertEqual(experiment.created_by, GTest.user)

        experiment = ExperimentRunService.run_experiment(experiment=experiment)

        # Refresh the processes
        protocol: ProtocolModel = experiment.protocol_model
        self.assertEqual(protocol.created_by, GTest.user)

        p0: TaskModel = protocol.get_process("p0")
        self.assertEqual(protocol.created_by, GTest.user)

        p1: TaskModel = protocol.get_process("p1")
        p2: TaskModel = protocol.get_process("p2")
        p3: TaskModel = protocol.get_process("p3")
        p_wait: TaskModel = protocol.get_process("p_wait")
        elon: Robot = p0.outputs.get_resource_model('robot').get_resource()

        print(" \n------ Resource --------")

        self.assertEqual(elon.weight, 70)

        # check p1
        self.assertEqual(
            p1.outputs.get_resource_model('robot').get_resource().position[1],
            elon.position[1] + p1.config.get_value('moving_step'))
        self.assertEqual(p1.outputs.get_resource_model('robot').get_resource().weight, elon.weight)

        # check p2
        self.assertEqual(p2.outputs.get_resource_model('robot').get_resource().position,
                         p2.inputs.get_resource_model('robot').get_resource().position)
        self.assertEqual(p2.outputs.get_resource_model('robot').get_resource().weight, p2.inputs.get_resource_model(
            'robot').get_resource().weight + p2.config.get_value('food_weight'))

        # check p3
        self.assertEqual(p3.outputs.get_resource_model('robot').get_resource().position[1], p3.inputs.get_resource_model(
            'robot').get_resource().position[1] + p3.config.get_value('moving_step'))
        self.assertEqual(p3.outputs.get_resource_model('robot').get_resource().weight,
                         p3.inputs.get_resource_model('robot').get_resource().weight)

        res = ResourceModel.get_by_id(p3.outputs.get_resource_model('robot').id)
        self.assertTrue(isinstance(res, ResourceModel))

        self.assertTrue(
            len(p0.progress_bar.data["messages"]) >= 2)
        print(p0.progress_bar.data)

        print(" \n------ Experiment --------")
        print(experiment.to_json())

    def test_after_run(self):
        """Test that the after run method is called
        To test it, we check that it raised an exception
        """

        experiment: IExperiment = IExperiment()
        experiment.get_protocol().add_process(RunAfterTask, 'run')

        with self.assertRaises(Exception):
            experiment.run()
