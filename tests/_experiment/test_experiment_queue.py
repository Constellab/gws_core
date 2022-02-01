# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time

from gws_core import (BaseTestCase, Experiment, ExperimentService,
                      ExperimentStatus, GTest, QueueService, Settings)
from gws_core.impl.robot.robot_protocol import CreateSimpleRobot

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestExperiment(BaseTestCase):

    init_before_each_test: bool = True

    async def test_service(self):
        GTest.print("ExperimentService")
        experiment = ExperimentService.create_experiment_from_protocol_type(CreateSimpleRobot)
        count = Experiment.select().count()
        self.assertEqual(count, 1)

        QueueService.init(tick_interval=3, daemon=False)  # tick each 3 second

        self.assertEqual(Experiment.select().count(), 1)

        print("")
        print("Run the experiment ...")
        self.assertTrue(self._run(experiment.id))
        self.assertEqual(Experiment.select().count(), 1)

        print("Re-run the same experiment ...")
        experiment = experiment.refresh()
        self.assertTrue(self._run(experiment.id))
        self.assertEqual(Experiment.select().count(), 1)

        print("")
        print("Re-run the same experiment after its validation...")
        experiment2: Experiment = Experiment.get(
            Experiment.id == experiment.id)

        ExperimentService.validate_experiment(experiment2.id, GTest.create_default_project())
        self.assertFalse(self._run(experiment.id))
        self.assertEqual(Experiment.select().count(), 1)

    def _run(self, experiment_id: str) -> bool:
        try:
            QueueService.add_experiment_to_queue(
                experiment_id=experiment_id)
        except Exception as err:
            print(err)
            return False

        self.assertEqual(Experiment.count_of_running_experiments(), 1)
        n = 0
        while Experiment.count_of_running_experiments() > 0:
            print("Waiting 3 secs for cli experiment to finish ...")
            time.sleep(3)
            if n == 10:
                raise Exception("The experiment queue is not empty")
            n += 1

        self.assertEqual(Experiment.count_of_running_experiments(), 0)
        experiment1: Experiment = Experiment.get(
            Experiment.id == experiment_id)
        self.assertEqual(experiment1.status, ExperimentStatus.SUCCESS)
        self.assertEqual(experiment1.pid, 0)
        print("Done!")
        return True
