

import asyncio
import unittest
from gws.model import Job, Process, Protocol, Config, Experiment
from gws.controller import Controller
from gws.robot import create_nested_protocol

class TestJob(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Protocol.drop_table()
        Process.drop_table()
        Config.drop_table()
        Job.drop_table()
        Experiment.drop_table()
        
        Experiment.create_table()
        Protocol.create_table()
        Process.create_table()
        Config.create_table()
        Job.create_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Protocol.drop_table()
        Process.drop_table()
        Config.drop_table()
        Job.drop_table()
        Experiment.drop_table()
        pass

    def test_job(self):
        proc = Process(instance_name="proc")
        proc.save()

        j1 = Job(process=proc, config=Config())
        is_saved = j1.save()
        self.assertTrue(is_saved)

        j2 = Job.get(Job.id == j1.id)
        self.assertEqual(j1, j2)
    

    def test_job_flow(self):
        proto = create_nested_protocol()
        e = proto.create_experiment()
        
        def _on_end(*args, **kwargs):
            job_list = Job.select().where(Job.process_type == "gws.model.Protocol")
            for job in job_list:
                print("-------------------------------- flow")
                print( job.flow )
        
        e.on_end( _on_end )
        asyncio.run( e.run() )
        