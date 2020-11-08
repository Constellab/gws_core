

import asyncio
import unittest
from gws.model import Job, Process, Config, Experiment
from gws.controller import Controller

class TestJob(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Process.drop_table()
        Config.drop_table()
        Job.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Process.drop_table()
        Config.drop_table()
        Job.drop_table()
        pass

    def test_job(self):
        #e = Experiment()
        proc = Process()
        proc.save()

        j1 = Job(process=proc, config=Config())
        is_saved = j1.save()
        self.assertTrue(is_saved)

        j2 = Job.get(Job.id == j1.id)
        self.assertEqual(j1, j2)
