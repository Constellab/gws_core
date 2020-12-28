
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
        
        async def _run():
            e = Experiment(protocol=proto)
            await e.run()

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
        mini_proto = Protocol(
            title = "Mini travel",
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

        super_proto = Protocol(
            title = "Super travel",
            processes={
                "p0": p0,
                "p5": p5,
                "mini_proto": mini_proto
            },
            connectors=[
                p0>>'robot'        | mini_proto<<'robot',
                mini_proto>>'robot'     | p5<<'robot'
            ]
        )
        
        print("--- mini travel --- ")
        print(mini_proto.dumps(bare=True))
        print("--- super travel --- ")
        print(super_proto.dumps(bare=True))
        
        p1 = mini_proto.get_process("p1")
        mini_proto.is_interfaced_with(p1)
        p2 = mini_proto.get_process("p2")
        mini_proto.is_outerfaced_with(p2)

        with open(os.path.join(testdata_dir, "mini_travel_graph.json"), "r") as f:
            import json
            s1 = json.load(f)
            s2 = json.loads(mini_proto.dumps(bare=True))
            self.assertEqual(s1,s2)
            
        def _on_end(*args, **kwargs):
            saved_mini_proto = Protocol.get(Protocol.id == mini_proto.id)
            s3 = json.loads(mini_proto.dumps(bare=True))
            self.assertEqual(s1,s3)
            
            # load non-bare
            mini_proto2 = Protocol.from_graph(saved_mini_proto.graph)
            self.assertTrue(mini_proto.graph, mini_proto2.graph)
        
        async def _run():
            e = super_proto.create_experiment()
            e.on_end(_on_end)
            await e.run()

            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)

        asyncio.run( _run() )

    def test_graph_load(self):
        return
        with open(os.path.join(testdata_dir, "mini_travel_graph.json"), "r") as f:
            import json
            s1 = json.load(f)
            mini_proto = Protocol.from_graph(s1)
            s2 = json.loads(mini_proto.dumps(bare=True))
            self.assertEqual(s1,s2)

        p1 = mini_proto.get_process("p1")
        self.assertTrue(mini_proto.is_interfaced_with(p1))

        p2 = mini_proto.get_process("p2")
        self.assertTrue(mini_proto.is_outerfaced_with(p2))

        p0 = Create(name="p0")
        p5 = Eat(name="p5")

        super_proto = Protocol(
            processes={
                "p0": p0,
                "p5": p5,
                "mini_proto": mini_proto
            },
            connectors=[
                p0>>'robot'        | mini_proto<<'robot',
                mini_proto>>'robot'     | p5<<'robot'
            ]
        )

        def _on_end(*args, **kwargs):
            saved_mini_proto = Protocol.get(Protocol.id == super_mini_proto.id)
            print(saved_mini_proto.as_json())
            
            # load none bare
            mini_proto2 = Protocol(graph=saved_mini_proto.graph)
            self.assertTrue(mini_proto.graph, mini_proto2.graph)
            
            
        async def _run():
            e = super_proto.create_experiment()
            e.on_end(_on_end)
            await e.run()

            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)
            
        asyncio.run( _run() )