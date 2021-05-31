# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import asyncio
import unittest
import json
import time

from gws.settings import Settings
from gws.model import *
from gws.queue import *
from gws.robot import *
from gws.unittest import GTest

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")

class TestQueue(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        tables = ( 
            Resource, Create, Config,
            Process, Protocol, Experiment, 
            Robot, Study, User, Activity, 
            ProgressBar, Queue, Job
        )
        GTest.drop_tables(tables)
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        #tables = ( Create, Config, Process, Protocol, Experiment, Robot, Study, User, Activity, ProgressBar, )
        #GTest.drop_tables(tables)
        pass
    
    def test_queue(self):
        self.assertEqual(Experiment.count_of_running_experiments(), 0)
        self.assertEqual(Queue.length(),0)
        
        proto1 = create_nested_protocol()
        e1 = Experiment(protocol=proto1, study=GTest.study, user=GTest.user)
        e1.save()
        job1 = Job(user=GTest.user, experiment=e1)
        Queue.add(job1)
        
        self.assertEqual(Queue.next(),job1)
        self.assertEqual(Queue.length(),1)
        
        proto2 = create_nested_protocol()
        e2 = Experiment(protocol=proto2, study=GTest.study, user=GTest.user)
        e2.save()
        job2 = Job(user=GTest.user, experiment=e2)
        Queue.add(job2)
        
        self.assertEqual(Queue.next(),job1)
        self.assertEqual(Queue.length(),2)
        
        Queue.remove(job1)
        self.assertEqual(Queue.next(),job2)
        self.assertEqual(Queue.length(),1)
        
        proto3 = create_nested_protocol()
        e3 = Experiment(protocol=proto3, study=GTest.study, user=GTest.user)
        e3.save()
        job3 = Job(user=GTest.user, experiment=e3)
        Queue.add(job3)
        self.assertEqual(Queue.next(),job2)
        self.assertEqual(Queue.length(),2)
        
        Queue.init(tick_interval=1, verbose=True) # tick each second
  
        n = 0
        while Queue.length():
            print("Waiting 3 secs for cli experiments to finish ...")
            time.sleep(3)
            if n == 10:
                raise Error("The experiment queue is not empty")
            n += 1

        Q = Experiment.select()
        self.assertEqual(len(Q), 3)
        for e in Q: 
            if e.id == e1.id:
                # check that e1 has never been run
                self.assertEqual(e.is_finished, False)
            else:
                self.assertEqual(e.is_finished, True)
            