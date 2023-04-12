# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os

from gws_core import (BaseTestCase, Experiment, ExperimentService,
                      ExperimentStatus, ProtocolModel, ProtocolService, Robot,
                      RobotFood, TaskModel)
from gws_core.data_provider.data_provider import DataProvider
from gws_core.experiment.experiment_run_service import ExperimentRunService
from tests.protocol_examples import (TestNestedProtocol,
                                     TestRobotWithSugarProtocol,
                                     TestSimpleProtocol)


# test_protocol
class TestProtocol(BaseTestCase):

    init_before_each_test: bool = True

    def test_protocol(self):

        query = ProtocolModel.select()
        count = len(query)

        # create a chain
        proto: ProtocolModel = ProtocolService.create_protocol_model_from_type(
            TestSimpleProtocol)

        query = ProtocolModel.select()
        self.assertEqual(len(query), count+1)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=proto)

        experiment = ExperimentRunService.run_experiment(experiment=experiment)

        self.assertEqual(len(experiment.task_models), 7)
        self.assertEqual(experiment.status, ExperimentStatus.SUCCESS)

    def test_advanced_protocol(self):

        query = ProtocolModel.select()
        count = len(query)

        super_proto: ProtocolModel = ProtocolService.create_protocol_model_from_type(
            TestNestedProtocol)

        query = ProtocolModel.select()
        self.assertEqual(ProtocolModel.select().count(), count+2)
        self.assertEqual(len(query), count+2)

        query = ProtocolModel.select()
        self.assertEqual(ProtocolModel.select().count(), count+2)
        self.assertEqual(len(query), count+2)

        query = ProtocolModel.select()
        self.assertEqual(ProtocolModel.select().count(), count+2)

        mini_proto: ProtocolModel = super_proto.get_process('mini_proto')
        p1 = mini_proto.get_process("p1")
        self.assertTrue(mini_proto.is_interfaced_with(p1.instance_name))
        p2 = mini_proto.get_process("p2")
        self.assertTrue(mini_proto.is_outerfaced_with(p2.instance_name))

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=super_proto)

        self.assertEqual(ProtocolModel.select().count(), count+2)

        experiment = ExperimentRunService.run_experiment(experiment=experiment)

        super_proto = ProtocolModel.get_by_id(super_proto.id)

        query = ProtocolModel.select()
        self.assertEqual(len(query), count+2)

    def test_graph_load(self):

        super_proto: ProtocolModel
        with open(DataProvider.get_test_data_path("super_proto_update.json"), "r") as file:
            s1 = json.load(file)
            super_proto = ProtocolService.create_protocol_model_from_graph(s1)

        self.assertEqual(len(super_proto.processes), 4)
        self.assertEqual(len(super_proto.connectors), 3)
        self.assertTrue("mini_travel" in super_proto.processes)

        mini_travel: ProtocolModel = super_proto.processes["mini_travel"]
        # check mini travel
        sub_p1 = mini_travel.get_process("p1")
        self.assertTrue(mini_travel.is_interfaced_with(sub_p1.instance_name))

        sub_p2 = mini_travel.get_process("p2")
        self.assertTrue(mini_travel.is_outerfaced_with(sub_p2.instance_name))

    def test_optional_input(self):
        """Test the optional input if different scenarios
        1. It is connected and provided, so we wait for it
        2. It is not connected
        3. It is connected but not provided (None)
        """
        protocol: ProtocolModel = ProtocolService.create_protocol_model_from_type(
            TestRobotWithSugarProtocol)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=protocol)

        experiment = ExperimentRunService.run_experiment(experiment=experiment)

        eat_1: TaskModel = experiment.protocol_model.get_process('eat_1')
        food: RobotFood = eat_1.inputs.get_resource_model('food')

        self.assertIsNotNone(food)

        # check that the RobotEat used the sugar food.
        # if yes, this will mean that the process eat waited for the food process to end
        # even if the food input of eat is optional
        robot_input: Robot = eat_1.inputs.get_resource_model(
            'robot').get_resource()
        robot_output: Robot = eat_1.outputs.get_resource_model(
            'robot').get_resource()
        # 2 = food weight, 10 sugar multiplicator
        self.assertEqual(robot_output.weight, robot_input.weight + (2 * 10))

        # Check that the eat_2 was called even if the food input (optional) is not plug
        eat_2: TaskModel = experiment.protocol_model.get_process('eat_2')
        robot_output_2: Robot = eat_2.outputs.get_resource_model(
            'robot').get_resource()
        # If this doesn't work, this mean that the process eat_2 was not called because it misses an optional input
        self.assertEqual(robot_output_2.weight,
                         robot_output.weight + 5)  # 5 = food weight
