
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
        return
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

        super_proto = Protocol(
            title = "super_proto",
            processes={
                "p0": p0,
                "p5": p5,
                "proto": proto
            },
            connectors=[
                p0>>'robot'        | proto<<'robot',
                proto>>'robot'     | p5<<'robot'
            ]
        )
        
        print(proto.dumps(bare=True))
        
        p1 = proto.get_process("p1")
        proto.is_interfaced_with(p1)
        p2 = proto.get_process("p2")
        proto.is_outerfaced_with(p2)

        with open(os.path.join(testdata_dir, "protocol_graph.json"), "r") as f:
            import json
            s1 = json.load(f)
            s2 = json.loads(proto.dumps(bare=True))
            self.assertEqual(s1,s2)
            
        
        def _on_end(*args, **kwargs):
            saved_proto = Protocol.get(Protocol.id == proto.id)
            s3 = json.loads(proto.dumps(bare=True))
            self.assertEqual(s1,s3)
            
            # load none bare
            proto2 = Protocol.from_graph(saved_proto.graph)
            self.assertTrue(proto.graph, proto2.graph)
        
        async def _run():
            e = super_proto.create_experiment()
            e.on_end(_on_end)
            await e.run()

            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)

        asyncio.run( _run() )

    def test_graph_load(self):
        with open(os.path.join(testdata_dir, "protocol_graph.json"), "r") as f:
            import json
            s1 = json.load(f)
            proto = Protocol.from_graph(s1)

            s2 = json.loads(proto.dumps(bare=True))
            self.assertEqual(s1,s2)

        p1 = proto.get_process("p1")
        self.assertTrue(proto.is_interfaced_with(p1))

        p2 = proto.get_process("p2")
        self.assertTrue(proto.is_outerfaced_with(p2))

        p0 = Create(name="p0")
        p5 = Eat(name="p5")

        super_proto = Protocol(
            processes={
                "p0": p0,
                "p5": p5,
                "proto": proto
            },
            connectors=[
                p0>>'robot'        | proto<<'robot',
                proto>>'robot'     | p5<<'robot'
            ]
        )

        def _on_end(*args, **kwargs):
            saved_proto = Protocol.get(Protocol.id == super_proto.id)
            print(saved_proto.as_json())
            
            # load none bare
            proto2 = Protocol(graph=saved_proto.graph)
            self.assertTrue(proto.graph, proto2.graph)
            
            
        async def _run():
            e = super_proto.create_experiment()
            e.on_end(_on_end)
            await e.run()

            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)
            
        asyncio.run( _run() )