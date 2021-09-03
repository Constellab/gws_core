# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from typing import List

from gws_core import (BaseTestCase, Experiment, ExperimentDTO,
                      ExperimentService, ExperimentStatus, GTest,
                      ProcessableModel, ProcessModel, ProtocolModel,
                      ResourceModel, Robot, RobotService, Settings)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestExperiment(BaseTestCase):

    init_before_each_test: bool = True

    async def test_create_empty(self):
        GTest.print("Create empty")
        experiment_dto: ExperimentDTO = ExperimentDTO(title="Experiment title", description="Experiment description")
        experiment = ExperimentService.create_empty_experiment(experiment_dto)

        self.assertIsNotNone(experiment.id)
        self.assertEqual(experiment.get_title(), 'Experiment title')
        self.assertEqual(experiment.get_description(), 'Experiment description')
        self.assertIsNotNone(experiment.protocol.id)

    async def test_run(self):
        GTest.print("Run Experiment")
        self.assertEqual(Experiment.count_of_running_experiments(), 0)

        # Create experiment 1
        # -------------------------------
        print("Create experiment 1")
        proto1: ProtocolModel = RobotService.create_robot_world_travel()

        experiment1: Experiment = ExperimentService.create_experiment_from_protocol(
            protocol=proto1, title="My exp title", description="This is my new experiment")

        #self.assertEqual(e1.processes.count(), 18)
        #self.assertEqual(Process.select().count(), 18)

        self.assertEqual(len(experiment1.processes), 15)
        self.assertEqual(ProcessModel.select().count(), 15)
        self.assertEqual(ResourceModel.select().count(), 0)
        self.assertEqual(Experiment.select().count(), 1)

        # Create experiment 2 = experiment 2
        # -------------------------------
        print("Create experiment_2 = experiment_1 ...")
        experiment2: Experiment = Experiment.get_by_uri_and_check(experiment1.uri)

        self.assertEqual(experiment2.get_title(), "My exp title")
        self.assertEqual(experiment2.get_description(),
                         "This is my new experiment")
        self.assertEqual(experiment2, experiment1)
        self.assertEqual(len(experiment2.processes), 15)
        self.assertEqual(ProcessModel.select().count(), 15)
        self.assertEqual(ResourceModel.select().count(), 0)
        self.assertEqual(Experiment.select().count(), 1)

        print("Run experiment_2 ...")
        experiment2 = await ExperimentService.run_experiment(experiment=experiment2, user=GTest.user)

        #self.assertEqual(e2.processes.count(), 18)
        self.assertEqual(len(experiment2.processes), 15)
        self.assertEqual(experiment2.status, ExperimentStatus.SUCCESS)

        Q1 = experiment1.resources
        Q2 = experiment2.resources
        self.assertEqual(ResourceModel.select().count(), 15)
        self.assertEqual(len(Q1), 15)
        self.assertEqual(len(Q2), 15)
        self.assertEqual(experiment2.pid, 0)

        e2_bis: Experiment = Experiment.get(Experiment.uri == experiment1.uri)

        self.assertEqual(e2_bis.get_title(), "My exp title")
        self.assertEqual(e2_bis.get_description(), "This is my new experiment")
        self.assertEqual(len(e2_bis.processes), 15)
        self.assertEqual(Experiment.select().count(), 1)

        # Test the configuration on fly_1 process (west 2000)
        fly_1: ProcessableModel = e2_bis.protocol.get_process('fly_1')
        robot1: Robot = fly_1.input.get_resource_model('robot').get_resource()
        robot2: Robot = fly_1.output.get_resource_model('robot').get_resource()
        self.assertEqual(robot1.position[0], robot2.position[0] + 2000)

        # Test the protocol (super_travel) config (weight of 10)
        super_travel: ProtocolModel = e2_bis.protocol.get_process('super_travel')
        eat_3: ProtocolModel = super_travel.get_process('eat_3')
        robot1: Robot = eat_3.input.get_resource_model('robot').get_resource()
        robot2: Robot = eat_3.output.get_resource_model('robot').get_resource()
        self.assertEqual(robot1.weight, robot2.weight - 10)

    async def test_run_through_cli_and_re_run(self):

        # experiment 3
        # -------------------------------
        print("Create experiment_3")
        proto3 = RobotService.create_robot_world_travel()
        experiment3 = ExperimentService.create_experiment_from_protocol(protocol=proto3)

        print("Run experiment_3 through cli ...")
        ExperimentService.run_through_cli(
            experiment=experiment3, user=GTest.user)
        self.assertEqual(experiment3.status,
                         ExperimentStatus.WAITING_FOR_CLI_PROCESS)
        self.assertTrue(experiment3.pid > 0)
        print(f"Experiment pid = {experiment3.pid}", )

        waiting_count = 0
        experiment3: Experiment = Experiment.get_by_uri_and_check(experiment3.uri)
        print(experiment3.protocol)
        while experiment3.status != ExperimentStatus.SUCCESS:
            print("Waiting 3 secs the experiment to finish ...")
            time.sleep(3)
            if waiting_count == 10:
                raise Exception("The experiment is not finished")
            experiment3.refresh()  # reload from DB
            waiting_count += 1

        self.assertEqual(Experiment.count_of_running_experiments(), 0)
        experiment3: Experiment = Experiment.get_by_uri_and_check(experiment3.uri)
        self.assertEqual(experiment3.status, ExperimentStatus.SUCCESS)
        self.assertEqual(experiment3.pid, 0)

        Q = experiment3.resources
        self.assertEqual(len(Q), 15)

        # archive experiment
        def _test_archive(tf):
            OK = experiment3.archive(tf)
            self.assertTrue(OK)
            resources: List[ResourceModel] = experiment3.resources
            self.assertEqual(len(resources), 15)
            for r in resources:
                self.assertEqual(r.is_archived, tf)

            processes: List[ProcessModel] = experiment3.processes
            #self.assertEqual( len(Q), 18)
            self.assertEqual(len(processes), 15)
            for process in processes:
                self.assertEqual(process.is_archived, tf)
                self.assertEqual(process.config.is_archived, tf)

        print("Archive experiment ...")
        _test_archive(True)

        print("Unarchive experiment ...")
        _test_archive(False)

        print("Archive experiment again...")
        _test_archive(True)
