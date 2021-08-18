# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Tuple
from unittest import IsolatedAsyncioTestCase

from gws_core import (Experiment, ExperimentService, GTest, ProcessModel,
                      Protocol, ProtocolModel, Robot, RobotCreate, RobotEat,
                      RobotMove, RobotWait)
from gws_core.process.processable_factory import ProcessableFactory
from gws_core.protocol.protocol_service import ProtocolService


class TestProcess(IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_process_singleton(self):
        GTest.print("Process Singleton")

        p0: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotCreate)
        p1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotCreate)
        # p0.title = "First 'Create' process"
        # p0.description = "This is the description of the process"
        p0.save_full()

        self.assertTrue(p0.id != p1.id)

    async def test_process(self):
        GTest.print("Process")

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
                p0.out_port('robot') | p1.in_port('robot'),
                p1.out_port('robot') | p2 << 'robot',
                p2 >> 'robot' | p_wait << 'robot',
                p_wait >> 'robot' | p3 << 'robot',
                p3 >> 'robot' | p4 << 'robot',
                p2 >> 'robot' | p5 << 'robot'
            ],
            interfaces={},
            outerfaces={}
        )

        self.assertTrue(p0.created_by.is_sysuser)
        self.assertEqual(proto.created_by, GTest.user)

        self.assertEqual(len(p1.get_next_procs()), 1)
        self.assertEqual(len(p2.get_next_procs()), 2)

        p2.set_param('food_weight', '5.6')

        experiment: Experiment = ExperimentService.create_experiment_from_protocol(
            protocol=proto)

        self.assertEqual(experiment.created_by, GTest.user)
        self.assertEqual(experiment.study, GTest.study)

        experiment = await ExperimentService.run_experiment(
            experiment=experiment, user=GTest.user)

        elon = p0.output['robot']

        print(" \n------ Resource --------")
        print(elon.to_json())

        self.assertEqual(elon.weight, 70)
        self.assertEqual(elon, p1.input['robot'])
        self.assertTrue(elon is p1.input['robot'])

        # check p1
        self.assertEqual(
            p1.output['robot'].position[1], elon.position[1] + p1.get_param('moving_step'))
        self.assertEqual(p1.output['robot'].weight, elon.weight)

        # check p2
        self.assertEqual(
            p1.output['robot'], p2.input['robot'])
        self.assertEqual(p2.output['robot'].position,
                         p2.input['robot'].position)
        self.assertEqual(
            p2.output['robot'].weight, p2.input['robot'].weight + p2.get_param('food_weight'))

        # check p3
        self.assertEqual(
            p_wait.output['robot'], p3.input['robot'])
        self.assertEqual(p3.output['robot'].position[1],
                         p3.input['robot'].position[1] + p3.get_param('moving_step'))
        self.assertEqual(p3.output['robot'].weight,
                         p3.input['robot'].weight)

        res = Robot.get_by_id(p3.output['robot'].id)
        self.assertTrue(isinstance(res, Robot))

        self.assertTrue(
            len(p0.progress_bar.data["messages"]) >= 2)
        print(p0.progress_bar.data)

        print(" \n------ Experiment --------")
        print(experiment.to_json())
