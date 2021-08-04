# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import time
import unittest

from gws_core import (Experiment, GTest, Job, Queue, QueueService,
                      RobotService, Settings)

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")


class TestQueue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_queue(self):
        GTest.print("Experiment Queue")

        self.assertEqual(Experiment.count_of_running_experiments(), 0)
        self.assertEqual(Queue.length(), 0)

        proto1 = RobotService.create_nested_protol()
        e1 = Experiment(protocol=proto1, study=GTest.study, user=GTest.user)
        e1.save()
        job1 = Job(user=GTest.user, experiment=e1)
        QueueService.add_job(job1)

        self.assertEqual(Queue.next(), job1)
        self.assertEqual(Queue.length(), 1)

        proto2 = RobotService.create_nested_protol()
        e2 = Experiment(protocol=proto2, study=GTest.study, user=GTest.user)
        e2.save()
        job2 = Job(user=GTest.user, experiment=e2)
        QueueService.add_job(job2)

        self.assertEqual(Queue.next(), job1)
        self.assertEqual(Queue.length(), 2)

        Queue.remove(job1)
        self.assertEqual(Queue.next(), job2)
        self.assertEqual(Queue.length(), 1)

        proto3 = RobotService.create_nested_protol()
        e3 = Experiment(protocol=proto3, study=GTest.study, user=GTest.user)
        e3.save()
        job3 = Job(user=GTest.user, experiment=e3)
        QueueService.add_job(job3)
        self.assertEqual(Queue.next(), job2)
        self.assertEqual(Queue.length(), 2)

        Queue.init(tick_interval=1, verbose=True)  # tick each second

        n = 0
        while Queue.length():
            print("Waiting 3 secs for cli experiments to finish ...")
            time.sleep(3)
            if n == 10:
                raise Exception("The experiment queue is not empty")
            n += 1

        Q = Experiment.select()
        self.assertEqual(len(Q), 3)
        for e in Q:
            if e.id == e1.id:
                # check that e1 has never been run
                self.assertEqual(e.is_finished, False)
            else:
                self.assertEqual(e.is_finished, True)

        Queue.deinit()
        time.sleep(3)
