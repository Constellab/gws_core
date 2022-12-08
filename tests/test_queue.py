# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import time

from gws_core import (BaseTestCase, Experiment, ExperimentService,
                      ExperimentStatus, GTest, Queue, QueueService,
                      RobotService, Settings)

settings = Settings.get_instance()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestQueue(BaseTestCase):

    def test_queue(self):

        queue: Queue = Queue().save()
        self.assertEqual(Experiment.count_running_or_queued_experiments(), 0)
        self.assertEqual(queue.length(), 0)

        proto1 = RobotService.create_robot_world_travel()
        experiment1: Experiment = ExperimentService.create_experiment_from_protocol_model(protocol_model=proto1)
        Queue.add_job(user=GTest.user, experiment=experiment1)

        experiment1 = experiment1.refresh()
        self.assertEqual(experiment1.status, ExperimentStatus.IN_QUEUE)

        self.assertEqual(Queue.length(), 1)
        job1 = queue.pop_first()
        self.assertEqual(Queue.length(), 0)
        self.assertEqual(experiment1.id, job1.experiment.id)

        Queue.add_job(user=GTest.user, experiment=experiment1)
        self.assertEqual(Queue.length(), 1)
        Queue.remove_experiment(experiment1.id)
        self.assertEqual(Queue.length(), 0)

        experiment1 = experiment1.refresh()
        self.assertEqual(experiment1.status, ExperimentStatus.DRAFT)

    def test_queue_run(self):
        # init the ticking, tick each second
        QueueService.init(tick_interval=3)

        proto2 = RobotService.create_robot_world_travel()
        experiment2: Experiment = ExperimentService.create_experiment_from_protocol_model(protocol_model=proto2)

        proto3 = RobotService.create_robot_world_travel()
        experiment3: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=proto3)

        QueueService._add_job(user=GTest.user, experiment=experiment2)
        QueueService._add_job(user=GTest.user, experiment=experiment3)

        self.assertEqual(Queue.length(), 2)
        self._wait_for_experiments()
        self.assertEqual(Queue.length(), 0)

        experiment2 = experiment2.refresh()
        experiment3 = experiment3.refresh()
        self.assertEqual(experiment2.status, ExperimentStatus.SUCCESS)
        self.assertEqual(experiment3.status, ExperimentStatus.SUCCESS)

        # Re-run exp3
        QueueService.add_experiment_to_queue(experiment2.id)
        self._wait_for_experiments()

        experiment3 = experiment3.refresh()
        self.assertEqual(experiment3.status, ExperimentStatus.SUCCESS)

    def _wait_for_experiments(self) -> None:

        wait_count = 0
        # Wait until the queue is clear and there is not experiment that is running
        while Queue.length() > 0 or Experiment.count_running_or_queued_experiments() > 0:
            print("Waiting 5 secs for cli experiments to finish ...")
            time.sleep(5)
            if wait_count >= 10:
                raise Exception("The experiment queue is not empty")
            wait_count += 1
