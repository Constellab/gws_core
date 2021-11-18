# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import time

from gws_core import (BaseTestCase, Experiment, ExperimentService,
                      ExperimentStatus, GTest, Job, Queue, QueueService,
                      RobotService, Settings)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestQueue(BaseTestCase):

    def test_queue(self):
        GTest.print("Experiment Queue")

        self.assertEqual(Experiment.count_of_running_experiments(), 0)
        self.assertEqual(Queue.length(), 0)

        proto1 = RobotService.create_robot_world_travel()
        experiment1 = ExperimentService.create_experiment_from_protocol_model(protocol_model=proto1)
        job1 = Job(user=GTest.user, experiment=experiment1)
        QueueService.add_job(job1)

        self.assertEqual(Queue.next(), job1)
        self.assertEqual(Queue.length(), 1)

        proto2 = RobotService.create_robot_world_travel()
        experiment2 = ExperimentService.create_experiment_from_protocol_model(protocol_model=proto2)
        job2 = Job(user=GTest.user, experiment=experiment2)
        QueueService.add_job(job2)

        self.assertEqual(Queue.next(), job1)
        self.assertEqual(Queue.length(), 2)

        Queue.remove(job1)
        self.assertEqual(Queue.next(), job2)
        self.assertEqual(Queue.length(), 1)

        proto3 = RobotService.create_robot_world_travel()
        experiment3 = ExperimentService.create_experiment_from_protocol_model(protocol_model=proto3)
        job3 = Job(user=GTest.user, experiment=experiment3)
        QueueService.add_job(job3)
        self.assertEqual(Queue.next(), job2)
        self.assertEqual(Queue.length(), 2)

        # init the ticking, tick each second
        QueueService.init(tick_interval=3)
        wait_count = 0
        # Wait until the queue is clear and there is not experiment that is running
        while Queue.length() > 0 or ExperimentService.count_of_running_experiments() > 0:
            print("Waiting 5 secs for cli experiments to finish ...")
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
