

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
        pass

    def test_experiment(self):
        e = Experiment()
        proc = Process()
        proc.save()

        e = Job(process=proc, config=Config())
        is_saved = e.save()

        self.assertTrue(is_saved)
