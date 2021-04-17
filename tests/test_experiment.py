
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

class TestExperiment(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        tables = ( Resource, Create, Config, Process, Protocol, Experiment, Robot, Study, User, Activity, ProgressBar, )
        GTest.drop_tables(tables)
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        #tables = ( Create, Config, Process, Protocol, Experiment, Robot, Study, User, Activity, ProgressBar, )
        #GTest.drop_tables(tables)
        pass
    
    def test_run(self):
        self.assertEqual(Experiment.count_of_experiments_in_progress(), 0)
        
        # Create experiment 1
        # -------------------------------
        print("Create experiment 1")
        proto1 = create_nested_protocol()
        e1 = Experiment(protocol=proto1, study=GTest.study, user=GTest.user)
        self.assertEqual(e1.processes.count(), 18)
        self.assertEqual(Process.select().count(), 18)
        self.assertEqual(Resource.select().count(), 0)

        # Create experiment 2 = experiment 2
        # -------------------------------
        print("Create experiment_2 = experiment_1 ...")
        e2 = Experiment.get(Experiment.uri == e1.uri)
        self.assertEqual(e2, e1)
        
        def _check_exp1(*args, **kwargs):
            self.assertEqual(e2.processes.count(), 18)
            self.assertEqual(e2.is_finished, False)
            self.assertEqual(e2.is_running, True)
        
        e2.on_end(_check_exp1)
        print("Run experiment_2 ...")
        asyncio.run( e2.run(user=GTest.user) )
        
        Q1 = e1.resources
        Q2 = e2.resources
        self.assertEqual(len(Q1),15)
        self.assertEqual(len(Q2),15)
        
        time.sleep(2)
        self.assertEqual(e2.pid, 0)
        self.assertEqual(e2.processes.count(), 18)
        self.assertEqual(e2.is_finished, True)
        self.assertEqual(e2.is_running, False)
        
        # experiment 3
        # -------------------------------
        print("Create experiment_3")
        proto3 = create_nested_protocol()
        e3 = Experiment(protocol=proto3, study=GTest.study, user=GTest.user)
        e3.save()        
        
        print("Run experiment_3 through cli ...")
        e3.run_through_cli(user=GTest.user)
        self.assertTrue(e3.pid > 0)
        self.assertEqual(e3.is_finished, False)
        self.assertEqual(e3.is_running, False)
        print(f"Experiment pid = {e3.pid}", )
        
        print("Waiting 5 secs for cli experiment to finish ...")
        time.sleep(5)
        self.assertEqual(Experiment.count_of_experiments_in_progress(), 0)
        e3 = Experiment.get(Experiment.id == e3.id)
        self.assertEqual(e3.is_finished, True)
        self.assertEqual(e3.is_running, False)
        self.assertEqual(e3.pid, 0)
        
        
        Q = e3.resources
        self.assertEqual(len(Q),15)
        
