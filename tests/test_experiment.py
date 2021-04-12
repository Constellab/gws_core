
import os
import asyncio
import unittest
import json
import time

from gws.settings import Settings
from gws.model import *
from gws.controller import Controller
from gws.robot import *
from gws.unittest import GTest

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")

class TestProtocol(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        tables = ( Create, Config, Process, Protocol, Experiment, Job, Robot, Study, User, Activity, ProgressBar, )
        GTest.drop_tables(tables)
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        #tables = ( Create, Config, Process, Protocol, Experiment, Job, Robot, Study, User, Activity, ProgressBar, )
        #GTest.drop_tables(tables)
        pass
    
    def test_run(self):
        study = Study.get_by_id(1)
          
        # experiment 1
        # -------------------------------
        print("Run experiment 1 ...")
        proto1 = create_nested_protocol()
        e0 = Experiment(protocol=proto1, study=GTest.study, user=GTest.user)
        e0.save()
        
        self.assertEqual(e0.jobs.count(), 18)
        self.assertEqual(Job.select().count(), 18)
        
        # retrieve experiment and check that it is the same
        e1 = Experiment.from_flow(e0.generate_flow())
        #e1 = Experiment.get(Experiment.uri == e0.uri).compile()
        #self.assertEqual(e1, e0)
        #self.assertEqual(e1.job, e0.job)
        
        self.assertEqual(e1.jobs.count(), 18)
        self.assertEqual(Job.select().count(), 36)
        
        def _check_exp1(*args, **kwargs):
            self.assertEqual(e1.jobs.count(), 18)
            self.assertEqual(e1.is_finished, True)
            self.assertEqual(e1.is_running, False)
        
        e1.save()
        e1.on_end(_check_exp1)
        asyncio.run( e1.run(user=GTest.user) )
        
        #for job in e1.jobs:
        #    self.assertEqual(job.experiment, e1)
            
        time.sleep(2)
        self.assertEqual(e1.pid, 0)
        self.assertEqual(e1.jobs.count(), 18)
        self.assertEqual(e1.is_finished, True)
        self.assertEqual(e1.is_running, False)
        
        # experiment 2
        # -------------------------------
        print("Run experiment 2 through cli ...")
        proto2 = create_nested_protocol()
        e2 = Experiment(protocol=proto2, study=GTest.study, user=GTest.user)
        #def _check_exp2(*args, **kwargs):
        #    self.assertEqual(e2.jobs.count(), 18)
        #    self.assertEqual(e2.is_finished, True)
        #    self.assertEqual(e2.is_running, False)
    
        e2.save()
        #e2.on_end(_check_exp2)
        
        e2.run_cli(user=GTest.user, is_test=True)
        self.assertTrue(e2.pid > 0)
        self.assertEqual(e2.is_finished, False)
        self.assertEqual(e2.is_running, False)
        print(f"Experiment pid = {e2.pid}", )
        
        print("Waiting 2 secs for cli experiment to finish ...")
        time.sleep(2)
        e3 = Experiment.get(Experiment.id == e2.id)
        self.assertEqual(e3.is_finished, True)
        self.assertEqual(e3.is_running, False)
        self.assertEqual(e3.pid, 0)
        
        
