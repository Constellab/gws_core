
import os
import asyncio
import unittest
import json

from gws.settings import Settings
from gws.model import Config, Process, Resource, Model, ViewModel, Protocol, Job, Experiment
from gws.controller import Controller
from gws.robot import Robot, create_nested_protocol

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
    
    def test_robot(self):
        proto = create_nested_protocol()
        e = proto.create_experiment()
        
        async def _run():
            await e.run()
            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)
        
        asyncio.run( _run() )
        
        print(e.protocol)
  