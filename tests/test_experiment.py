
import os
import asyncio
import unittest
import json

from gws.settings import Settings
from gws.model import Config, Process, Resource, Model, ViewModel, Protocol, Job, Experiment, Study, User
from gws.controller import Controller
from gws.robot import Robot, Create, Move, Eat, Wait, create_nested_protocol
from gws.unittest import GTest


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
        Study.drop_table()
        User.drop_table()
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        Config.drop_table()
        Process.drop_table()
        Protocol.drop_table()
        Experiment.drop_table()
        Job.drop_table()
        Robot.drop_table()
        Study.drop_table()
        User.drop_table()
        pass

    def test_experiment(self):
        study = Study.get_default_instance()
        proto = create_nested_protocol()    
        e = proto.create_experiment(study=GTest.study,user=GTest.user)
        e.save()
        flow = e.flow
  
        #flow["study_uri"] = ""
        #self.assertRaises( Exception, Experiment.from_flow, flow )
        
        #flow["experiment_uri"] = ""
        #flow["study_uri"] = study.uri
        #Experiment.from_flow(flow)
        
        
        print(e.flow)
        
        
        
        