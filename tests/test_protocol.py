
import os
import asyncio
import unittest
import json

from gws.settings import Settings
from gws.model import Config, Process, Resource, Model, ViewModel, Protocol, Job, Experiment
from gws.controller import Controller
from gws.robot import Robot, Create, Move, Eat, Wait

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")

class TestProtocol(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Config.drop_table()
        Process.drop_table()
        Protocol.drop_table()
        Experiment.drop_table()
        Job.drop_table()
        Robot.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Config.drop_table()
        Process.drop_table()
        Protocol.drop_table()
        Experiment.drop_table()
        Job.drop_table()
        Robot.drop_table()
        pass
    
    def test_protocol(self):
        p0 = Create()
        p1 = Move()
        p2 = Eat()
        p3 = Move()
        p4 = Move()
        p5 = Eat()
        p_wait = Wait()
 
        # create a chain
        proto = Protocol(
            processes = {
                'p0' : p0,  
                'p1' : p1, 
                'p2' : p2, 
                'p3' : p3,  
                'p4' : p4,  
                'p5' : p5, 
                'p_wait' : p_wait
            },
            connectors=[
                p0>>'robot'        | p1<<'robot',
                p1>>'robot'        | p2<<'robot',
                p2>>'robot'        | p_wait<<'robot',
                p_wait>>'robot'    | p3<<'robot',
                p3>>'robot'        | p4<<'robot',
                p2>>'robot'        | p5<<'robot'
            ],
            interfaces = {},
            outerfaces = {}
        )
        
        proto.set_active_experiment(Experiment())

        async def _run():
            await proto.run()

            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)

        def _check_exp():
            e = proto.get_active_experiment()
            self.assertEqual(e.jobs.count(), 8)
            self.assertEqual(e.is_finished, False)
            self.assertEqual(e.is_running, False)

        proto.on_end = _check_exp

        asyncio.run( _run() )

    def test_setting_dump(self):
        p0 = Create(title="p0")
        p1 = Move()
        p2 = Eat()
        p3 = Move()
        p4 = Move()
        p5 = Eat(title="p5")
        p_wait = Wait()
    
        # create a chain
        proto = Protocol(
            title = "proto",
            processes = {
                'p1' : p1, 
                'p2' : p2, 
                'p3' : p3,  
                'p4' : p4,  
                'p_wait' : p_wait
            },
            connectors=[
                p1>>'robot'        | p2<<'robot',
                p2>>'robot'        | p_wait<<'robot',
                p_wait>>'robot'    | p3<<'robot',
                p2>>'robot'        | p4<<'robot'
            ],
            interfaces = { 'robot' : p1.in_port('robot') },
            outerfaces = { 'robot' : p2.out_port('robot') }
        )

        proto.set_active_experiment(Experiment())
        
        p0>>'robot'        | proto<<'robot'
        proto>>'robot'     | p5<<'robot'

        p1 = proto.get_process("p1")
        proto.is_interfaced_with(p1)
        p2 = proto.get_process("p2")
        proto.is_outerfaced_with(p2)

        with open(os.path.join(testdata_dir, "protocol_graph.json"), "r") as f:
            import json
            s1 = json.load(f)
            s2 = json.loads(proto.dumps())
            self.assertEqual(s1,s2)

        async def _run():
            await p0.run()

            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)

        asyncio.run( _run() )

    def test_graph_load(self):
        with open(os.path.join(testdata_dir, "protocol_graph.json"), "r") as f:
            import json
            s1 = json.load(f)
            proto = Protocol(graph=s1)

            s2 = json.loads(proto.dumps())
            self.assertEqual(s1,s2)

        p1 = proto.get_process("p1")
        proto.is_interfaced_with(p1)

        p2 = proto.get_process("p2")
        proto.is_outerfaced_with(p2)

        p0 = Create(name="p0")
        p5 = Eat(name="p5")

        p0>>'robot'        | proto<<'robot'
        proto>>'robot'     | p5<<'robot'

        proto.set_active_experiment(Experiment())
        async def _run():
            await p0.run()

            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)
            
        asyncio.run( _run() )