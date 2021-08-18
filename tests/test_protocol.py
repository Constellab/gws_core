# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
from unittest import IsolatedAsyncioTestCase

from gws_core import (Experiment, ExperimentService, ExperimentStatus, GTest,
                      ProcessableFactory, ProcessModel, ProtocolModel,
                      ProtocolService, RobotCreate, RobotEat, RobotMove,
                      RobotWait, Settings)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestProtocol(IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    async def test_protocol(self):
        GTest.print("Protocol")

        p0: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotCreate)
        p1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        p2: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotEat)
        p3: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        p4: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        p5: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotEat)
        p_wait: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotWait)

        Q = ProtocolModel.select()
        count = len(Q)

        # create a chain
        proto: ProtocolModel = ProtocolService.create_protocol_from_data(
            processes={
                'p0': p0,
                'p1': p1,
                'p2': p2,
                'p3': p3,
                'p4': p4,
                'p5': p5,
                'p_wait': p_wait
            },
            connectors=[
                p0 >> 'robot' | p1 << 'robot',
                p1 >> 'robot' | p2 << 'robot',
                p2 >> 'robot' | p_wait << 'robot',
                p_wait >> 'robot' | p3 << 'robot',
                p3 >> 'robot' | p4 << 'robot',
                p2 >> 'robot' | p5 << 'robot'
            ],
            interfaces={},
            outerfaces={}
        )

        Q = ProtocolModel.select()
        self.assertEqual(len(Q), count+1)

        experiment: Experiment = Experiment(
            protocol=proto, study=GTest.study, user=GTest.user)

        experiment.save()

        experiment = await ExperimentService.run_experiment(
            experiment=experiment, user=GTest.user)

        self.assertEqual(len(experiment.processes), 7)
        self.assertEqual(experiment.status, ExperimentStatus.SUCCESS)

    async def test_advanced_protocol(self):
        GTest.print("Advanced protocol")
        p0: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotCreate, instance_name="p0")
        p1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        p2: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotEat)
        p3: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        p4: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        p5: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotEat, instance_name="p5")
        p_wait: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotWait)

        Q = ProtocolModel.select()
        count = len(Q)

        # create a chain
        mini_proto: ProtocolModel = ProtocolService.create_protocol_from_data(
            processes={
                'p1': p1,
                'p2': p2,
                'p3': p3,
                'p4': p4,
                'p_wait': p_wait
            },
            connectors=[
                p1 >> 'robot' | p2 << 'robot',
                p2 >> 'robot' | p_wait << 'robot',
                p_wait >> 'robot' | p3 << 'robot',
                p2 >> 'robot' | p4 << 'robot'
            ],
            interfaces={'robot': p1.in_port('robot')},
            outerfaces={'robot': p2.out_port('robot')}
        )

        Q = ProtocolModel.select()
        self.assertEqual(len(Q), count+1)

        super_proto: ProtocolModel = ProtocolService.create_protocol_from_data(
            processes={
                "p0": p0,
                "p5": p5,
                "mini_travel": mini_proto
            },
            connectors=[
                p0 >> 'robot' | mini_proto << 'robot',
                mini_proto >> 'robot' | p5 << 'robot'
            ]
        )

        Q = ProtocolModel.select()
        self.assertEqual(ProtocolModel.select().count(), count+2)
        self.assertEqual(len(Q), count+2)

        # print("--- mini travel --- ")
        # print(mini_proto.dumps(bare=True))

        Q = ProtocolModel.select()
        self.assertEqual(ProtocolModel.select().count(), count+2)
        self.assertEqual(len(Q), count+2)

        # print("--- super travel --- ")
        # print(super_proto.dumps(bare=True))

        Q = ProtocolModel.select()
        self.assertEqual(ProtocolModel.select().count(), count+2)

        p1 = mini_proto.get_process("p1")
        mini_proto.is_interfaced_with(p1)
        p2 = mini_proto.get_process("p2")
        mini_proto.is_outerfaced_with(p2)

        with open(os.path.join(testdata_dir, "mini_travel_graph.json"), "r") as f:
            s1 = json.load(f)
            s2 = json.loads(json.dumps(mini_proto.dumps(bare=True)))
            self.assertEqual(s1, s2)  # TODO a améliorer, car ça casse vite

        experiment: Experiment = ExperimentService.create_experiment_from_protocol(
            protocol=super_proto)

        self.assertEqual(ProtocolModel.select().count(), count+2)

        experiment = await ExperimentService.run_experiment(
            experiment=experiment, user=GTest.user)

        mini_proto_reloaded: ProtocolModel = ProtocolModel.get_by_id(
            mini_proto.id)

        super_proto = ProtocolModel.get_by_id(super_proto.id)

        s3 = json.loads(json.dumps(mini_proto_reloaded.dumps(bare=True)))
        self.assertEqual(s3, s1)
        Q = ProtocolModel.select()
        self.assertEqual(len(Q), count+2)

    async def test_graph_load(self):
        GTest.print("Load protocol graph")

        mini_proto: ProtocolModel
        with open(os.path.join(testdata_dir, "mini_travel_graph.json"), "r") as f:
            s1 = json.load(f)
            mini_proto = ProtocolService.create_protocol_from_graph(s1)
            s2 = mini_proto.dumps(bare=True)
            self.assertEqual(s1, s2)

        p1 = mini_proto.get_process("p1")
        self.assertTrue(mini_proto.is_interfaced_with(p1))

        p2 = mini_proto.get_process("p2")
        self.assertTrue(mini_proto.is_outerfaced_with(p2))

        p0: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotCreate)
        p5: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotEat)

        super_proto: ProtocolModel = ProtocolService.create_protocol_from_data(
            processes={
                "p0": p0,
                "p5": p5,
                "Mini travel": mini_proto
            },
            connectors=[
                p0 >> 'robot' | mini_proto << 'robot',
                mini_proto >> 'robot' | p5 << 'robot'
            ]
        )

        experiment: Experiment = ExperimentService.create_experiment_from_protocol(
            protocol=super_proto)

        experiment = await ExperimentService.run_experiment(
            experiment=experiment, user=GTest.user)

        saved_mini_proto = ProtocolModel.get(ProtocolModel.id == mini_proto.id)
        # load none bare
        mini_proto2 = ProcessableFactory.create_protocol_from_graph(
            saved_mini_proto.graph)
        self.assertTrue(mini_proto.graph, mini_proto2.graph)

    # TODO improve test because it does not test connection create or deletion
    async def test_protocol_update(self):
        GTest.print("Update protocol")
        p0: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotCreate)
        p1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        p2: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotEat)
        p3: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        p4: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        p5: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotEat)
        p_wait: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotWait)

        # create a chain
        mini_proto: ProtocolModel = ProtocolService.create_protocol_from_data(
            processes={
                'p1': p1,
                'p2': p2,
                'p3': p3,
                'p4': p4,
                'p_wait': p_wait
            },
            connectors=[
                p1 >> 'robot' | p2 << 'robot',
                p2 >> 'robot' | p_wait << 'robot',
                p_wait >> 'robot' | p3 << 'robot',
                p2 >> 'robot' | p4 << 'robot'
            ],
            interfaces={'robot': p1.in_port('robot')},
            outerfaces={'robot': p2.out_port('robot')}
        )

        super_proto: ProtocolModel = ProtocolService.create_protocol_from_data(
            processes={
                "p0": p0,
                "p5": p5,
                "mini_travel": mini_proto
            },
            connectors=[
                p0 >> 'robot' | mini_proto << 'robot',
                mini_proto >> 'robot' | p5 << 'robot'
            ]
        )

        # Check the correct number of processes
        super_proto_db: ProtocolModel = ProtocolService.get_protocol_by_uri(
            super_proto.uri)
        mini_proto_db: ProtocolModel = super_proto_db.processes["mini_travel"]
        self.assertEqual(len(mini_proto_db.processes), 5)

        # Update the protocol by adding a process to the mini proto
        new_wait: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotWait)
        # remove the uri to simulate the real json from a request
        new_wait.uri = None
        mini_proto.add_process("new_wait", new_wait)
        # revresh the graph to get the json
        mini_proto.data["graph"] = mini_proto.dumps()
        json_dump = super_proto.dumps()

        ProtocolService.update_protocol_graph(
            protocol=super_proto_db, graph=json_dump)

        # Check that the process was added
        mini_proto_db: ProtocolModel = ProtocolService.get_protocol_by_uri(
            mini_proto.uri)

        self.assertEqual(len(mini_proto_db.processes), 6)

        mini_proto: ProtocolModel = super_proto.processes["mini_travel"]
        mini_proto.delete_process("new_wait")
        # refrehs the graph to get the json
        mini_proto.data["graph"] = mini_proto.dumps()
        ProtocolService.update_protocol_graph(
            protocol=super_proto_db, graph=super_proto.dumps())

        # Check that the process was added
        mini_proto_db: ProtocolModel = ProtocolService.get_protocol_by_uri(
            mini_proto.uri)

        self.assertEqual(len(mini_proto_db.processes), 5)
