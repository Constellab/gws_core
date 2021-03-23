
import os
import asyncio
import unittest
import json

from gws.settings import Settings
from gws.model import Config, Process, Resource, Model, ViewModel, Protocol, Job, Experiment, Study
from gws.controller import Controller
from gws.robot import Robot, Create, Move, Eat, Wait, create_nested_protocol


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
        
        study = Study(data={"title": "Default study", "Description": ""})
        study.save()
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

    def test_experiment(self):
        study = Study.get_default_instance()
        proto = create_nested_protocol()    
        e = proto.create_experiment(study=study)
        e.save()
        flow = e.flow
  
        #flow["study_uri"] = ""
        #self.assertRaises( Exception, Experiment.from_flow, flow )
        
        #flow["experiment_uri"] = ""
        #flow["study_uri"] = study.uri
        #Experiment.from_flow(flow)
        
        
        print(e.flow)
        
        
        
        