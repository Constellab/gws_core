
import os
import asyncio
import unittest
import json
from collections import OrderedDict

from gws.controller import Controller
from gws.settings import Settings
from gws.model import Job, Process, Protocol, Config, Experiment, Study, User
from gws.robot import create_nested_protocol
from gws.unittest import GTest

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")


class TestJob(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Protocol.drop_table()
        Process.drop_table()
        Config.drop_table()
        Job.drop_table()
        Experiment.drop_table()
        Study.drop_table()
        User.drop_table()
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        Protocol.drop_table()
        Process.drop_table()
        Config.drop_table()
        Job.drop_table()
        Experiment.drop_table()
        Study.drop_table()
        User.drop_table()
        pass

    def test_job(self):
        return
        proc = Process(instance_name="proc")
        proc.save()

        j1 = Job(process=proc, config=Config())
        is_saved = j1.save()
        self.assertTrue(is_saved)

        j2 = Job.get(Job.id == j1.id)
        self.assertEqual(j1, j2)
    

    def test_write_load_job_flow(self):    
        proto = create_nested_protocol()    
        e = proto.create_experiment(study=GTest.study,user=GTest.user)
        
        def compare_links(l1, l2):
            return l1["from"] == l2["from"] and  l1["to"] == l2["to"]
    
        def _on_end(*args, **kwargs):
            # load flow using protocol uri
            flow = proto.job.flow
            
            print(json.dumps(flow))
            
            print(f" PROTO ---------------")
            print(Protocol.barefy(proto.dumps()))
            
            print(f" PROTO 2 ---------------")
            proto2 = Protocol.from_flow(flow)
            print(Protocol.barefy(proto2.dumps()))
            
            s1 = Protocol.barefy(proto.dumps())
            s2 = Protocol.barefy(proto2.dumps())                
            self.assertEqual(s1, s2)

            # load bare flow
            flow["uri"] = ""
            flow["process"]["uri"] = ""
            proto3 = Protocol.from_flow(flow)
            print(f" PROTO 3 ---------------")
            print(Protocol.barefy(proto3.dumps()))
            
            a1 = Protocol.barefy(proto3.dumps())
            a2 = Protocol.barefy(proto.dumps())
            
            # compare without link because link orders have changed
            links1 = a1["links"]
            links2 = a2["links"]
            
            del a1["links"]
            del a2["links"]
            self.assertEqual(a1, a2)
            
            # check that links are the same
            OK = [ len(links1) == len(links2) ]
            for l1 in links1:
                OK.append(False)
                for l2 in links2:
                    if compare_links(l1,l2):
                        OK[-1] = True
                        break
            self.assertTrue(all(OK))
            
        e.on_end( _on_end )
        asyncio.run( e.run(user=GTest.user) )
    
    
    def test_load_job_flow_and_update(self):  
        return
        proto = create_nested_protocol()    
        e = proto.create_experiment(study=GTest.study,user=GTest.user)
        
        def _on_end(*args, **kwargs):
            flow = proto.job.flow
            f2 = flow.copy()
            
            # delete one link
            f2["process"]["uri"] = ""
            link = f2["flows"].pop(2)
            proto2 = Protocol.from_flow(f2)
            
            # load protocol: uri is empty => new protocol
            proto3 = Protocol.from_flow(f2)
            self.assertNotEqual(proto2, proto3)
            
            # load protocol: uri is not empty => update protocol
            f2["process"]["uri"] = proto2.uri
            f2["flows"].append(link)
            proto4 = Protocol.from_flow(f2)
            self.assertEqual(proto2, proto4)
            
        e.on_end( _on_end )
        asyncio.run( e.run(user=GTest.user) )
        
