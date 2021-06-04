# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import asyncio
import unittest
import json

from gws.settings import Settings
from gws.model import *
from gws.robot import Robot, Create, Move, Eat, Wait
from gws.comment import Comment
from gws.unittest import GTest

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")
tables = ( Resource, Create, Config, Process, Protocol, Experiment, Robot, Study, User, Activity, ProgressBar, Comment, )

class TestProtocol(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables(tables)
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        #GTest.drop_tables(tables)
        pass
    
    def test_protocol(self):
        return
        study = Study.get_by_id(1)
        
        p0 = Create()
        p1 = Move()
        p2 = Eat()
        p3 = Move()
        p4 = Move()
        p5 = Eat()
        p_wait = Wait()
         
        Q = Protocol.select()
        count = len(Q)
        
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
        
        
        Q = Protocol.select()
        self.assertEqual(len(Q), count+1)
        
        e = Experiment(protocol=proto, study=GTest.study, user=GTest.user)
        
        # check data the flow is well saved in DB
        # self.assertEqual(e.generate_flow(), e.data["flow"])
        
        def _check_exp(*args, **kwargs):
            self.assertEqual(e.processes.count(), 8)
            self.assertEqual(e.is_finished, False)
            self.assertEqual(e.is_running, True)

        e.on_end(_check_exp)
        e.save()
        
        asyncio.run( e.run(user=GTest.user) )

    def test_setting_dump(self):
        return
        study = Study.get_by_id(1)
        
        p0 = Create(instance_name="p0")
        p1 = Move()
        p2 = Eat()
        p3 = Move()
        p4 = Move()
        p5 = Eat(instance_name="p5")
        p_wait = Wait()
        
        Q = Protocol.select()
        count = len(Q)
        
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
        
        Q = Protocol.select()
        self.assertEqual(len(Q), count+1)
        
        super_proto = Protocol(
            title = "Super travel",
            processes={
                "p0": p0,
                "p5": p5,
                "mini_travel": mini_proto
            },
            connectors=[
                p0>>'robot'        | mini_proto<<'robot',
                mini_proto>>'robot'     | p5<<'robot'
            ]
        )
        
        Q = Protocol.select()
        self.assertEqual(Protocol.select().count(), count+2)
        self.assertEqual(len(Q), count+2)
        
        print("--- mini travel --- ")
        print(mini_proto.dumps(bare=True))
        
        Q = Protocol.select()
        self.assertEqual(Protocol.select().count(), count+2)
        self.assertEqual(len(Q), count+2)
        
        print("--- super travel --- ")
        print(super_proto.dumps(bare=True))
        
        Q = Protocol.select()
        self.assertEqual(Protocol.select().count(), count+2)
        
        p1 = mini_proto.get_process("p1")
        mini_proto.is_interfaced_with(p1)
        p2 = mini_proto.get_process("p2")
        mini_proto.is_outerfaced_with(p2)
    
        with open(os.path.join(testdata_dir, "mini_travel_graph.json"), "r") as f:
            s1 = json.load(f)
            s2 = json.loads(mini_proto.dumps(bare=True))
            self.assertEqual(s1,s2)
            
        e = super_proto.create_experiment(study=GTest.study, user=GTest.user)
        
        def _on_end(*args, **kwargs):
            
            #print("---- reload mini travel ----")
            mini_proto_reloaded = Protocol.get_by_id(mini_proto.id)
            #print(mini_proto_reloaded.dumps())
            
            s3 = json.loads(mini_proto_reloaded.dumps(bare=True))
            self.assertEqual(s1,s3)
            Q = Protocol.select()
            self.assertEqual(len(Q), count+2)
 
        e.on_end(_on_end)
        Q = Protocol.select()
        self.assertEqual(Protocol.select().count(), count+2)
            
        asyncio.run( e.run(user=GTest.user) )

    def test_graph_load(self):
        return
        study = Study.get_by_id(1)
        
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

        def _on_end(*args, **kwargs):
            saved_mini_proto = Protocol.get(Protocol.id == mini_proto.id)
            print(saved_mini_proto.to_json())
            
            # load none bare
            mini_proto2 = Protocol.from_graph(saved_mini_proto.graph)
            self.assertTrue(mini_proto.graph, mini_proto2.graph)
            
        e = super_proto.create_experiment(study=GTest.study, user=GTest.user)
        e.on_end(_on_end)    
        asyncio.run( e.run(user=GTest.user) )

    def test_update_protocol(self):
        with open(os.path.join(testdata_dir, "mini_travel_graph.json"), "r") as f:
            graph = json.load(f)

        mini_proto = Protocol.from_graph(graph)
        p = mini_proto.get_process("p1")
        self.assertEquals(p.config.get_param("moving_step"), 0.1)

        graph = mini_proto.dumps(as_dict=True)
        graph["nodes"]["p1"]["config"]["data"]["params"] = {}
        graph["nodes"]["p1"]["config"]["data"]["params"]["moving_step"] = 3.14
        mini_proto2 = Protocol.from_graph(graph)
        p2 = mini_proto2.get_process("p1")
        self.assertEquals(mini_proto2, mini_proto)
        self.assertEquals(p2.config, p.config)
        self.assertEquals(p2.config.get_param("moving_step"), 3.14)

        