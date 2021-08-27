# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os

from gws_core import (Experiment, ExperimentService, ExperimentStatus, GTest,
                      ProtocolModel, ProtocolService, Settings)

from tests.base_test import BaseTest
from tests.protocol_examples import TestNestedProtocol, TestSimpleProtocol

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestProtocol(BaseTest):

    async def test_protocol(self):
        GTest.print("Protocol")

        Q = ProtocolModel.select()
        count = len(Q)

        # create a chain
        proto: ProtocolModel = ProtocolService.create_protocol_from_type(TestSimpleProtocol)

        Q = ProtocolModel.select()
        self.assertEqual(len(Q), count+1)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol(
            protocol=proto)

        experiment = await ExperimentService.run_experiment(
            experiment=experiment, user=GTest.user)

        self.assertEqual(len(experiment.processes), 7)
        self.assertEqual(experiment.status, ExperimentStatus.SUCCESS)

    async def test_advanced_protocol(self):
        GTest.print("Advanced protocol")

        Q = ProtocolModel.select()
        count = len(Q)

        super_proto: ProtocolModel = ProtocolService.create_protocol_from_type(TestNestedProtocol)

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

        experiment: Experiment = ExperimentService.create_experiment_from_protocol(
            protocol=super_proto)

        self.assertEqual(ProtocolModel.select().count(), count+2)

        experiment = await ExperimentService.run_experiment(
            experiment=experiment, user=GTest.user)

        super_proto = ProtocolModel.get_by_id(super_proto.id)

        Q = ProtocolModel.select()
        self.assertEqual(len(Q), count+2)

    async def test_graph_load(self):
        GTest.print("Load protocol graph")

        super_proto: ProtocolModel
        with open(os.path.join(testdata_dir, "super_proto_update.json"), "r") as f:
            s1 = json.load(f)
            super_proto = ProtocolService.create_protocol_from_graph(s1)

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

        with open(os.path.join(testdata_dir, "super_proto.json"), "r") as f:
            s1 = json.load(f)
            super_proto = ProtocolService.create_protocol_from_graph(s1)

        super_proto_db = ProtocolService.get_protocol_by_uri(super_proto.uri)

        self.assertEqual(len(super_proto_db.processes), 2)
        self.assertEqual(len(super_proto_db.connectors), 0)
        self.assertTrue("p0" in super_proto_db.processes)
        self.assertTrue("p5" in super_proto_db.processes)

        # This file should add a mini travel sub protocol
        with open(os.path.join(testdata_dir, "super_proto_update.json"), "r") as f:
            s1 = json.load(f)
            super_proto = ProtocolService.update_protocol_graph(super_proto_db, s1)

        self.assertEqual(len(super_proto_db.processes), 4)
        self.assertEqual(len(super_proto_db.connectors), 3)
        self.assertTrue("mini_travel" in super_proto_db.processes)

        mini_travel_db: ProtocolModel = super_proto_db.processes["mini_travel"]
        # check mini travel
        self.assertEqual(len(mini_travel_db.processes), 2)
        self.assertEqual(len(mini_travel_db.connectors), 1)

        # Rollback to first protocol
        with open(os.path.join(testdata_dir, "super_proto.json"), "r") as f:
            s1 = json.load(f)
            super_proto = ProtocolService.update_protocol_graph(super_proto_db, s1)

        self.assertEqual(len(super_proto_db.processes), 2)
        self.assertEqual(len(super_proto_db.connectors), 0)
        self.assertTrue("p0" in super_proto_db.processes)
        self.assertTrue("p5" in super_proto_db.processes)
