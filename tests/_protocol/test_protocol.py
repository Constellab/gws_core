# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os

from gws_core import (BaseTestCase, Config, Experiment, ExperimentService,
                      ExperimentStatus, GTest, ProcessModel, ProgressBar,
                      ProtocolModel, ProtocolService, Robot, RobotFood,
                      RobotMove, Settings, TaskModel, Typing)
from gws_core.experiment.experiment_run_service import ExperimentRunService
from tests.protocol_examples import (TestNestedProtocol,
                                     TestRobotWithSugarProtocol,
                                     TestSimpleProtocol)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestProtocol(BaseTestCase):

    init_before_each_test: bool = True

    async def test_protocol(self):
        GTest.print("Protocol")

        Q = ProtocolModel.select()
        count = len(Q)

        # create a chain
        proto: ProtocolModel = ProtocolService.create_protocol_model_from_type(TestSimpleProtocol)

        Q = ProtocolModel.select()
        self.assertEqual(len(Q), count+1)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=proto)

        experiment = await ExperimentRunService.run_experiment(experiment=experiment)

        self.assertEqual(len(experiment.task_models), 7)
        self.assertEqual(experiment.status, ExperimentStatus.SUCCESS)

    async def test_advanced_protocol(self):
        GTest.print("Advanced protocol")

        Q = ProtocolModel.select()
        count = len(Q)

        super_proto: ProtocolModel = ProtocolService.create_protocol_model_from_type(TestNestedProtocol)

        Q = ProtocolModel.select()
        self.assertEqual(ProtocolModel.select().count(), count+2)
        self.assertEqual(len(Q), count+2)

        Q = ProtocolModel.select()
        self.assertEqual(ProtocolModel.select().count(), count+2)
        self.assertEqual(len(Q), count+2)

        Q = ProtocolModel.select()
        self.assertEqual(ProtocolModel.select().count(), count+2)

        mini_proto: ProtocolModel = super_proto.get_process('mini_proto')
        p1 = mini_proto.get_process("p1")
        self.assertTrue(mini_proto.is_interfaced_with(p1))
        p2 = mini_proto.get_process("p2")
        self.assertTrue(mini_proto.is_outerfaced_with(p2))

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=super_proto)

        self.assertEqual(ProtocolModel.select().count(), count+2)

        experiment = await ExperimentRunService.run_experiment(experiment=experiment)

        super_proto = ProtocolModel.get_by_id(super_proto.id)

        Q = ProtocolModel.select()
        self.assertEqual(len(Q), count+2)

    async def test_graph_load(self):
        GTest.print("Load protocol graph")

        super_proto: ProtocolModel
        with open(os.path.join(testdata_dir, "super_proto_update.json"), "r") as f:
            s1 = json.load(f)
            super_proto = ProtocolService.create_protocol_model_from_graph(s1)

        self.assertEqual(len(super_proto.processes), 4)
        self.assertEqual(len(super_proto.connectors), 3)
        self.assertTrue("mini_travel" in super_proto.processes)

        mini_travel: ProtocolModel = super_proto.processes["mini_travel"]
        # check mini travel
        sub_p1 = mini_travel.get_process("p1")
        self.assertTrue(mini_travel.is_interfaced_with(sub_p1))

        sub_p2 = mini_travel.get_process("p2")
        self.assertTrue(mini_travel.is_outerfaced_with(sub_p2))

    async def test_protocol_update(self):
        GTest.print("Update protocol")

        with open(os.path.join(testdata_dir, "super_proto.json"), "r") as file:
            s1 = json.load(file)
            super_proto = ProtocolService.create_protocol_model_from_graph(s1)

        super_proto_db = ProtocolService.get_protocol_by_id(super_proto.id)

        self.assertEqual(len(super_proto_db.processes), 2)
        self.assertEqual(len(super_proto_db.connectors), 0)
        self.assertTrue("p0" in super_proto_db.processes)
        self.assertTrue("p5" in super_proto_db.processes)

        p0: TaskModel = super_proto_db.get_process('p0')
        p5: TaskModel = super_proto_db.get_process('p5')

        # This file should add a mini travel sub protocol
        with open(os.path.join(testdata_dir, "super_proto_update.json"), "r") as file:
            # set the p0 and p5 id to simulate a real update
            file_content: str = file.read().replace('p0_id', p0.id).replace('p5_id', p5.id)
            s1 = json.loads(file_content)
            super_proto = ProtocolService.update_protocol_graph(super_proto_db, s1)

        super_proto_db = ProtocolService.get_protocol_by_id(super_proto.id)

        self.assertEqual(len(super_proto_db.processes), 4)
        self.assertEqual(len(super_proto_db.connectors), 3)
        self.assertTrue("mini_travel" in super_proto_db.processes)

        mini_travel_db: ProtocolModel = super_proto_db.get_process("mini_travel")
        # check mini travel
        self.assertEqual(len(mini_travel_db.processes), 2)
        self.assertEqual(len(mini_travel_db.connectors), 1)

        # check that p0 and p5 did not change id
        self.assertEqual(super_proto_db.get_process('p0').id, p0.id)
        self.assertEqual(super_proto_db.get_process('p5').id, p5.id)

        # check p5 config was updated
        p5 = super_proto_db.get_process('p5')
        self.assertEqual(p5.config.get_value('food_weight'), 15)

        # Check the number of process, protocol, config and progress bar
        self.assertEqual(TaskModel.select().count(), 5)
        self.assertEqual(ProtocolModel.select().count(), 2)
        self.assertEqual(Config.select().count(), 7)
        self.assertEqual(ProgressBar.select().count(), 7)

        sub_p1: ProcessModel = mini_travel_db.get_process('p1')
        # Delete p2 of mini travel, update p1 config (of mini travel)
        with open(os.path.join(testdata_dir, "super_proto_update_2.json"), "r") as file:
            file_content: str = file.read().replace('p0_id', p0.id).replace('p5_id', p5.id)\
                .replace('mini_travel_id', mini_travel_db.id).replace('sub_p1_id', sub_p1.id)
            s1 = json.loads(file_content)
            super_proto = ProtocolService.update_protocol_graph(super_proto_db, s1)

        super_proto_db = ProtocolService.get_protocol_by_id(super_proto.id)
        mini_travel_db: ProtocolModel = super_proto_db.get_process("mini_travel")
        sub_p1: ProcessModel = mini_travel_db.get_process("p1")

        self.assertEqual(len(mini_travel_db.processes), 1)
        self.assertEqual(sub_p1.config.get_value("moving_step"), 20)

        # Rollback to first protocol
        with open(os.path.join(testdata_dir, "super_proto.json"), "r") as file:
            file_content: str = file.read().replace('p0_id', p0.id).replace('p5_id', p5.id)
            s1 = json.loads(file_content)
            super_proto = ProtocolService.update_protocol_graph(super_proto_db, s1)

        super_proto_db = ProtocolService.get_protocol_by_id(super_proto.id)

        self.assertEqual(len(super_proto_db.processes), 2)
        self.assertEqual(len(super_proto_db.connectors), 0)
        self.assertTrue("p0" in super_proto_db.processes)
        self.assertTrue("p5" in super_proto_db.processes)

        # Check that p5 config was cleared
        p5 = super_proto_db.get_process('p5')
        self.assertFalse(p5.config.value_is_set('food_weight'))

        # Check the number of process, protocol and config
        self.assertEqual(TaskModel.select().count(), 2)
        self.assertEqual(ProtocolModel.select().count(), 1)
        self.assertEqual(Config.select().count(), 3)
        self.assertEqual(ProgressBar.select().count(), 3)

    async def test_optional_input(self):
        """Test the optional input if different scenarios
        1. It is connected and provided, so we wait for it
        2. It is not connected
        3. It is connected but not provided (None)
        """
        protocol: ProtocolModel = ProtocolService.create_protocol_model_from_type(TestRobotWithSugarProtocol)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=protocol)

        experiment = await ExperimentRunService.run_experiment(experiment=experiment)

        eat_1: TaskModel = experiment.protocol_model.get_process('eat_1')
        food: RobotFood = eat_1.inputs.get_resource_model('food')

        self.assertIsNotNone(food)

        # check that the RobotEat used the sugar food.
        # if yes, this will mean that the process eat waited for the food process to end
        # even if the food input of eat is optional
        robot_input: Robot = eat_1.inputs.get_resource_model('robot').get_resource()
        robot_output: Robot = eat_1.outputs.get_resource_model('robot').get_resource()
        self.assertEqual(robot_output.weight, robot_input.weight + (2 * 10))  # 2 = food weight, 10 sugar multiplicator

        # Check that the eat_2 was called even if the food input (optional) is not plug
        eat_2: TaskModel = experiment.protocol_model.get_process('eat_2')
        robot_output_2: Robot = eat_2.outputs.get_resource_model('robot').get_resource()
        # If this doesn't work, this mean that the process eat_2 was not called because it misses an optional input
        self.assertEqual(robot_output_2.weight, robot_output.weight + 5)  # 5 = food weight
