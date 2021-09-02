# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, Experiment, ExperimentService, GTest,
                      Process, ProcessableFactory, ProcessDecorator,
                      ProcessInputs, ProcessModel, ProcessOutputs, ProgressBar,
                      ProtocolModel, ProtocolService, ResourceModel, Robot,
                      RobotCreate)
from gws_core.processable.processable_exception import ProcessableRunException

from tests.base_test import BaseTest
from tests.protocol_examples import TestSimpleProtocol


@ProcessDecorator("ErrorProcess")
class ErrorProcess(Process):
    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        raise Exception("Error")


class TestProcess(BaseTest):

    def test_process_singleton(self):
        GTest.print("Process Singleton")

        p0: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=RobotCreate)
        p1: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=RobotCreate)
        # p0.title = "First 'Create' process"
        # p0.description = "This is the description of the process"
        p0.save_full()

        self.assertTrue(p0.id != p1.id)

    async def test_process(self):
        GTest.print("Process")

        proto: ProtocolModel = ProtocolService.create_protocol_from_type(TestSimpleProtocol)

        p0: ProcessModel = proto.get_process('p0')
        p1: ProcessModel = proto.get_process('p1')
        p2: ProcessModel = proto.get_process('p2')

        self.assertTrue(p0.created_by.is_sysuser)
        self.assertEqual(proto.created_by, GTest.user)

        self.assertEqual(len(p1.output.get_next_procs()), 1)
        self.assertEqual(len(p2.output.get_next_procs()), 2)

        p2.config.set_param('food_weight', '5.6')

        experiment: Experiment = ExperimentService.create_experiment_from_protocol(
            protocol=proto)

        self.assertEqual(experiment.created_by, GTest.user)
        self.assertEqual(experiment.study, GTest.study)

        experiment = await ExperimentService.run_experiment(
            experiment=experiment, user=GTest.user)

        # Refresh the processes
        protocol: ProtocolModel = experiment.protocol
        p0: ProcessModel = protocol.get_process("p0")
        p1: ProcessModel = protocol.get_process("p1")
        p2: ProcessModel = protocol.get_process("p2")
        p3: ProcessModel = protocol.get_process("p3")
        p_wait: ProcessModel = protocol.get_process("p_wait")
        elon: Robot = p0.output.get_resource_model('robot').get_resource()

        print(" \n------ Resource --------")

        self.assertEqual(elon.weight, 70)

        # check p1
        self.assertEqual(
            p1.output.get_resource_model('robot').get_resource().position[1],
            elon.position[1] + p1.config.get_param('moving_step'))
        self.assertEqual(p1.output.get_resource_model('robot').get_resource().weight, elon.weight)

        # check p2
        self.assertEqual(p2.output.get_resource_model('robot').get_resource().position,
                         p2.input.get_resource_model('robot').get_resource().position)
        self.assertEqual(p2.output.get_resource_model('robot').get_resource().weight, p2.input.get_resource_model(
            'robot').get_resource().weight + p2.config.get_param('food_weight'))

        # check p3
        self.assertEqual(p3.output.get_resource_model('robot').get_resource().position[1], p3.input.get_resource_model(
            'robot').get_resource().position[1] + p3.config.get_param('moving_step'))
        self.assertEqual(p3.output.get_resource_model('robot').get_resource().weight,
                         p3.input.get_resource_model('robot').get_resource().weight)

        res = ResourceModel.get_by_id(p3.output.get_resource_model('robot').id)
        self.assertTrue(isinstance(res, ResourceModel))

        self.assertTrue(
            len(p0.progress_bar.data["messages"]) >= 2)
        print(p0.progress_bar.data)

        print(" \n------ Experiment --------")
        print(experiment.to_json())

    async def test_error_process(self):
        GTest.print("Error Process")

        p_error: ProcessModel = ProcessableFactory.create_process_model_from_type(process_type=ErrorProcess)

        experiment: Experiment = ExperimentService.create_experiment_from_process(p_error)

        with self.assertRaises(ProcessableRunException):
            await ExperimentService.run_experiment(
                experiment=experiment, user=GTest.user)
