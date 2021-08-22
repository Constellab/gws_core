# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import time
import unittest

from gws_core import (Experiment, ExperimentService, ExperimentStatus, GTest,
                      Job, Queue, QueueService, RobotService, Settings)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestQueue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        # kill the tick
        QueueService.deinit()
        GTest.drop_tables()

    def test_queue(self):
        GTest.print("Experiment Queue")

        self.assertEqual(Experiment.count_of_running_experiments(), 0)
        self.assertEqual(Queue.length(), 0)

        proto1 = RobotService.create_nested_protocol()
        experiment1 = Experiment(
            protocol=proto1, study=GTest.study, user=GTest.user)
        experiment1.save()
        job1 = Job(user=GTest.user, experiment=experiment1)
        QueueService.add_job(job1)

        self.assertEqual(Queue.next(), job1)
        self.assertEqual(Queue.length(), 1)

        proto2 = RobotService.create_nested_protocol()
        experiment2 = Experiment(
            protocol=proto2, study=GTest.study, user=GTest.user)
        experiment2.save()
        job2 = Job(user=GTest.user, experiment=experiment2)
        QueueService.add_job(job2)

        self.assertEqual(Queue.next(), job1)
        self.assertEqual(Queue.length(), 2)

        Queue.remove(job1)
        self.assertEqual(Queue.next(), job2)
        self.assertEqual(Queue.length(), 1)

        proto3 = RobotService.create_nested_protocol()
        experiment3 = Experiment(
            protocol=proto3, study=GTest.study, user=GTest.user)
        experiment3.save()
        job3 = Job(user=GTest.user, experiment=experiment3)
        QueueService.add_job(job3)
        self.assertEqual(Queue.next(), job2)
        self.assertEqual(Queue.length(), 2)

        # init the ticking, tick each second
        QueueService.init(tick_interval=3)
        wait_count = 0
        # Wait until the queue is clear and there is not experiment that is running
        while Queue.length() > 0 or ExperimentService.count_of_running_experiments() > 0:
            print("Waiting 3 secs for cli experiments to finish ...")
            time.sleep(5)
            if wait_count >= 10:
                raise Exception("The experiment queue is not empty")
            wait_count += 1

        query = Experiment.select()
        self.assertEqual(len(query), 3)
        for experiment in query:
            if experiment.id == experiment1.id:
                # check that e1 has never been run
                self.assertEqual(experiment.status, ExperimentStatus.DRAFT)
            else:
                self.assertEqual(experiment.status, ExperimentStatus.SUCCESS,
                                 f"Experiment {experiment.id} not finished")
