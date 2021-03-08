
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
    
    def test_flow_load(self):
        with open(os.path.join(testdata_dir, "super_travel_flow.json"), "r") as f:
            import json
            flow = json.load(f)
            
        
        proto = Protocol.from_flow(flow)
            
            
    def test_flow_load_gen(self):
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
                "Mini travel": mini_proto
            },
            connectors=[
                p0>>'robot'        | mini_proto<<'robot',
                mini_proto>>'robot'     | p5<<'robot'
            ]
        )
        
        e = super_proto.create_experiment()
        
        def _on_end(*args, **kwargs):
            import json
            print(json.dumps(e.flow))
            #print(e.flow)
        
        e.on_end(_on_end)            
        asyncio.run( e.run() )
        
        
        #flow = e.flow
        #self.assertEqual(flow, {})
        #print(flow)
        
        
        