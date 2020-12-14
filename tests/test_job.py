

import asyncio
import unittest
from gws.model import Job, Process, Protocol, Config, Experiment
from gws.controller import Controller
from gws.robot import create_nested_protocol

class TestJob(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Experiment.drop_table()
        Protocol.drop_table()
        Process.drop_table()
        Config.drop_table()
        Job.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Experiment.drop_table()
        Protocol.drop_table()
        Process.drop_table()
        Config.drop_table()
        Job.drop_table()
        pass

    def test_job(self):
        proc = Process()
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
                print("--------------------------------")
                print( job.flow )

        
        
        async def _run():
            await e.run()
            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)
        
        e.on_end( _on_end )
        asyncio.run( _run() )
        
        print(e.protocol)
        