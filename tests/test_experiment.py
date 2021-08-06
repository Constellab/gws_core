# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import time
import unittest

from gws_core import (Experiment, ExperimentService, ExperimentStatus, GTest,
                      Process, Queue, QueueService, Resource, RobotService,
                      Settings)

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")


class TestExperiment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()
        pass

    def test_run(self):
        GTest.print("Run Experiment")
        self.assertEqual(Experiment.count_of_running_experiments(), 0)

        # Create experiment 1
        # -------------------------------
        print("Create experiment 1")
        proto1 = RobotService.create_nested_protocol()
        experiment1: Experiment = Experiment(
            protocol=proto1, study=GTest.study, user=GTest.user)
        proto_title = proto1.get_title()
        experiment1.set_title("My exp title")
        experiment1.set_description("This is my new experiment")
        experiment1.save()

        #self.assertEqual(e1.processes.count(), 18)
        #self.assertEqual(Process.select().count(), 18)
        self.assertEqual(len(experiment1.processes), 15)
        self.assertEqual(Process.select().count(), 15)
        self.assertEqual(Resource.select().count(), 0)
        self.assertEqual(Experiment.select().count(), 1)

        # Create experiment 2 = experiment 2
        # -------------------------------
        print("Create experiment_2 = experiment_1 ...")
        experiment2: Experiment = Experiment.get(
            Experiment.uri == experiment1.uri)
        self.assertEqual(experiment2.protocol.get_title(), proto_title)
        self.assertEqual(experiment2.get_title(), "My exp title")
        self.assertEqual(experiment2.get_description(),
                         "This is my new experiment")
        self.assertEqual(experiment2, experiment1)
        self.assertEqual(len(experiment2.processes), 15)
        self.assertEqual(Process.select().count(), 15)
        self.assertEqual(Resource.select().count(), 0)
        self.assertEqual(Experiment.select().count(), 1)

        def _check_exp1(*args, **kwargs):
            #self.assertEqual(e2.processes.count(), 18)
            self.assertEqual(len(experiment2.processes), 15)
            self.assertEqual(experiment2.status, ExperimentStatus.RUNNING)

        experiment2.on_end(_check_exp1)
        print("Run experiment_2 ...")
        asyncio.run(experiment2.run(user=GTest.user))

        Q1 = experiment1.resources
        Q2 = experiment2.resources
        self.assertEqual(Resource.select().count(), 15)
        self.assertEqual(len(Q1), 15)
        self.assertEqual(len(Q2), 15)

        time.sleep(2)
        self.assertEqual(experiment2.pid, 0)
        #self.assertEqual(e2.processes.count(), 18)
        self.assertEqual(len(experiment2.processes), 15)
        self.assertEqual(experiment2.status, ExperimentStatus.SUCCESS)

        e2_bis: Experiment = Experiment.get(Experiment.uri == experiment1.uri)
        self.assertEqual(e2_bis.protocol.get_title(), proto_title)
        self.assertEqual(e2_bis.get_title(), "My exp title")
        self.assertEqual(e2_bis.get_description(), "This is my new experiment")
        self.assertEqual(len(e2_bis.processes), 15)
        self.assertEqual(Experiment.select().count(), 1)

        # experiment 3
        # -------------------------------
        print("Create experiment_3")
        proto3 = RobotService.create_nested_protocol()
        experiment3 = Experiment(
            protocol=proto3, study=GTest.study, user=GTest.user)
        experiment3.save()

        print("Run experiment_3 through cli ...")
        ExperimentService.run_through_cli(
            experiment=experiment3, user=GTest.user)
        self.assertTrue(experiment3.pid > 0)
        self.assertEqual(experiment3.status, False)
        self.assertEqual(experiment3.is_running, False)
        print(f"Experiment pid = {experiment3.pid}", )

        waiting_count = 0
        experiment3: Experiment = Experiment.get(
            Experiment.id == experiment3.id)
        while experiment3.status != ExperimentStatus.SUCCESS:
            print("Waiting 3 secs the experiment to finish ...")
            time.sleep(3)
            if waiting_count == 10:
                raise Exception("The experiment is not finished")
            waiting_count += 1

        self.assertEqual(Experiment.count_of_running_experiments(), 0)
        experiment3 = Experiment.get(Experiment.id == experiment3.id)
        self.assertEqual(experiment3.status, ExperimentStatus.SUCCESS)
        self.assertEqual(experiment3.pid, 0)

        Q = experiment3.resources
        self.assertEqual(len(Q), 15)

        # archive experiment
        def _test_archive(tf):
            OK = experiment3.archive(tf)
            self.assertTrue(OK)
            Q = experiment3.resources
            self.assertEqual(len(Q), 15)
            for r in Q:
                self.assertEqual(r.is_archived, tf)

            Q = experiment3.processes
            #self.assertEqual( len(Q), 18)
            self.assertEqual(len(Q), 15)
            for p in Q:
                self.assertEqual(p.is_archived, tf)
                self.assertEqual(p.config.is_archived, tf)

        print("Archive experiment ...")
        _test_archive(True)

        print("Unarchive experiment ...")
        _test_archive(False)

        print("Archive experiment again...")
        _test_archive(True)

    def test_service(self):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

        GTest.print("ExperimentService")
        proto = RobotService.create_nested_protocol()
        experiment = Experiment(
            protocol=proto, study=GTest.study, user=GTest.user)
        experiment.save()
        c = Experiment.select().count()
        self.assertEqual(c, 1)

        QueueService.init(tick_interval=3, verbose=True,
                          daemon=False)  # tick each second

        def _run() -> bool:
            try:
                asyncio.run(ExperimentService.start_experiment(experiment.uri))
            except:
                return False

            self.assertEqual(Queue.length(), 1)
            n = 0
            while Queue.length():
                print("Waiting 3 secs for cli experiment to finish ...")
                time.sleep(3)
                if n == 10:
                    raise Exception("The experiment queue is not empty")
                n += 1

            self.assertEqual(Experiment.count_of_running_experiments(), 0)
            experiment1: Experiment = Experiment.get(
                Experiment.id == experiment.id)
            self.assertEqual(experiment1.status, ExperimentStatus.SUCCESS)
            self.assertEqual(experiment1.pid, 0)
            print("Done!")
            return True

        self.assertEqual(Experiment.select().count(), 1)

        print("")
        print("Run the experiment ...")
        self.assertTrue(_run())
        self.assertEqual(Experiment.select().count(), 1)

        print("")
        print("Re-Run the same experiment ...")
        time.sleep(1)
        self.assertTrue(experiment.reset())
        self.assertTrue(_run())
        self.assertEqual(Experiment.select().count(), 1)

        print("")
        print("Re-Run the same experiment after its validation...")
        time.sleep(1)
        experiment2: Experiment = Experiment.get(
            Experiment.id == experiment.id)
        experiment2.validate(user=GTest.user)
        self.assertFalse(_run())
        self.assertEqual(Experiment.select().count(), 1)
        QueueService.deinit()
        time.sleep(3)
