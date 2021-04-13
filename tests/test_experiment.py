
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
        tables = ( Create, Config, Process, Protocol, Experiment, Robot, Study, User, Activity, ProgressBar, )
        GTest.drop_tables(tables)
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        #tables = ( Create, Config, Process, Protocol, Experiment, Robot, Study, User, Activity, ProgressBar, )
        #GTest.drop_tables(tables)
        pass
    
    def test_run(self):
        study = Study.get_by_id(1)
          
        # experiment 1
        # -------------------------------
        print("Run experiment 1 ...")
        proto1 = create_nested_protocol()
        e1 = Experiment(protocol=proto1, study=GTest.study, user=GTest.user)
        e1.save()

        e2 = Experiment.get(Experiment.uri == e1.uri)
        self.assertEqual(e1.processes.count(), 18)
        self.assertEqual(Process.select().count(), 18)
   
        def _check_exp1(*args, **kwargs):
            self.assertEqual(e1.processes.count(), 18)
            self.assertEqual(e1.is_finished, True)
            self.assertEqual(e1.is_running, False)
        
        e1.save()
        e1.on_end(_check_exp1)
        asyncio.run( e1.run(user=GTest.user) )
        
        Q = e1.resources
        self.assertEqual(len(Q),15)
        
        time.sleep(2)
        self.assertEqual(e1.pid, 0)
        self.assertEqual(e1.processes.count(), 18)
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
        e2.run_cli(user=GTest.user, is_test=True)
        self.assertTrue(e2.pid > 0)
        self.assertEqual(e2.is_finished, False)
        self.assertEqual(e2.is_running, False)
        print(f"Experiment pid = {e2.pid}", )
        
        print("Waiting 5 secs for cli experiment to finish ...")
        time.sleep(5)
        e3 = Experiment.get(Experiment.id == e2.id)
        self.assertEqual(e3.is_finished, True)
        self.assertEqual(e3.is_running, False)
        self.assertEqual(e3.pid, 0)
        
        
        Q = e3.resources
        self.assertEqual(len(Q),15)
        
