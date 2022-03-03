# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from typing import List

from gws_core import (BaseTestCase, Experiment, ExperimentDTO,
                      ExperimentService, ExperimentStatus, GTest, ProcessModel,
                      ProtocolModel, ResourceModel, Robot, RobotService,
                      RobotWorldTravelProto, Settings, TaskModel, Utils)
from gws_core.experiment.experiment_exception import \
    ResourceUsedInAnotherExperimentException
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_run_service import ExperimentRunService
from gws_core.impl.robot.robot_protocol import (CreateSimpleRobot,
                                                MoveSimpleRobot)
from gws_core.io.io_spec import IOSpecClass
from gws_core.process.process_model import ProcessStatus
from gws_core.project.project_dto import ProjectDto

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestExperiment(BaseTestCase):

    init_before_each_test: bool = True

    async def test_create_empty(self):

        project_dto: ProjectDto = ProjectDto(id=Utils.generate_uuid(), title="Project", description="Desc")
        experiment_dto: ExperimentDTO = ExperimentDTO(
            title="Experiment title", project=project_dto)
        experiment = ExperimentService.create_empty_experiment_from_dto(experiment_dto)

        self.assertIsNotNone(experiment.id)
        self.assertEqual(experiment.title, 'Experiment title')
        self.assertIsNotNone(experiment.protocol_model.id)
        self.assertEqual(experiment.project.id, project_dto.id)

        ExperimentService.update_experiment_description(experiment.id, {"test": "ok"})
        experiment = ExperimentService.get_experiment_by_id(experiment.id)
        self.assert_json(experiment.description, {"test": "ok"})

    async def test_run(self):
        self.assertEqual(Experiment.count_of_running_experiments(), 0)

        # Create experiment 1
        # -------------------------------
        print("Create experiment 1")
        proto1: ProtocolModel = RobotService.create_robot_world_travel()

        experiment1: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=proto1, title="My exp title")

        self.assertEqual(len(experiment1.task_models), 16)
        self.assertEqual(TaskModel.select().count(), 16)
        self.assertEqual(ResourceModel.select().count(), 0)
        self.assertEqual(Experiment.select().count(), 1)

        # Create experiment 2 = experiment 2
        # -------------------------------
        print("Create experiment_2 = experiment_1 ...")
        experiment2: Experiment = Experiment.get_by_id_and_check(experiment1.id)

        self.assertEqual(experiment2, experiment1)
        self.assertEqual(len(experiment2.task_models), 16)
        self.assertEqual(TaskModel.select().count(), 16)
        self.assertEqual(ResourceModel.select().count(), 0)
        self.assertEqual(Experiment.select().count(), 1)

        print("Run experiment_2 ...")
        experiment2 = await ExperimentRunService.run_experiment(experiment=experiment2)

        #self.assertEqual(e2.processes.count(), 18)
        self.assertEqual(len(experiment2.task_models), 16)
        self.assertEqual(experiment2.status, ExperimentStatus.SUCCESS)

        self.assertEqual(ResourceModel.select().count(), 15)
        self.assertEqual(len(experiment1.resources), 15)
        self.assertEqual(len(experiment2.resources), 15)
        self.assertEqual(ResourceModel.get_by_experiment(experiment1.id).count(), 15)
        self.assertEqual(experiment2.pid, 0)

        e2_bis: Experiment = ExperimentService.get_experiment_by_id(experiment1.id)

        self.assertEqual(e2_bis.title, "My exp title")
        self.assertEqual(len(e2_bis.task_models), 16)
        self.assertEqual(Experiment.select().count(), 1)

        # Test the configuration on fly_1 process (west 2000)
        fly_1: ProcessModel = e2_bis.protocol_model.get_process('fly_1')
        robot1: Robot = fly_1.inputs.get_resource_model('robot').get_resource()
        robot2: Robot = fly_1.outputs.get_resource_model('robot').get_resource()
        self.assertEqual(robot1.position[0], robot2.position[0] + 2000)

        # Check if the port resource spec was correctly loaded
        spec: IOSpecClass = fly_1.inputs.get_port('robot').resource_spec
        self.assertIsInstance(spec, IOSpecClass)
        self.assertEqual(spec.to_resource_types(), [Robot])

        # Test the protocol (super_travel) config (weight of 10)
        super_travel: ProtocolModel = e2_bis.protocol_model.get_process('super_travel')
        eat_3: ProtocolModel = super_travel.get_process('eat_3')
        robot1: Robot = eat_3.inputs.get_resource_model('robot').get_resource()
        robot2: Robot = eat_3.outputs.get_resource_model('robot').get_resource()
        self.assertEqual(robot1.weight, robot2.weight - 10)

    async def test_run_through_cli(self):

        # experiment 3
        # -------------------------------
        print("Create experiment_3")
        proto3 = RobotService.create_robot_world_travel()
        experiment3 = ExperimentService.create_experiment_from_protocol_model(protocol_model=proto3)

        print("Run experiment_3 through cli ...")
        ExperimentRunService.create_cli_process_for_experiment(
            experiment=experiment3, user=GTest.user)
        self.assertEqual(experiment3.status,
                         ExperimentStatus.WAITING_FOR_CLI_PROCESS)
        self.assertTrue(experiment3.pid > 0)
        print(f"Experiment pid = {experiment3.pid}", )

        waiting_count = 0
        experiment3: Experiment = Experiment.get_by_id_and_check(experiment3.id)
        print(experiment3.protocol_model)
        while experiment3.status != ExperimentStatus.SUCCESS:
            print("Waiting 3 secs the experiment to finish ...")
            time.sleep(3)
            if waiting_count == 10:
                raise Exception("The experiment is not finished")
            experiment3 = experiment3.refresh()  # reload from DB
            waiting_count += 1

        self.assertEqual(Experiment.count_of_running_experiments(), 0)
        experiment3 = Experiment.get_by_id_and_check(experiment3.id)
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

            processes: List[ProcessModel] = experiment3.task_models
            #self.assertEqual( len(Q), 18)
            self.assertEqual(len(processes), 16)
            for process in processes:
                self.assertEqual(process.is_archived, tf)
                self.assertEqual(process.config.is_archived, tf)

        print("Archive experiment ...")
        _test_archive(True)

        print("Unarchive experiment ...")
        _test_archive(False)

        print("Archive experiment again...")
        _test_archive(True)

    async def test_reset(self):
        experiment: Experiment = ExperimentService.create_experiment_from_protocol_type(RobotWorldTravelProto)

        experiment = await ExperimentRunService.run_experiment(experiment=experiment)

        experiment.reset()

        self.assertEqual(experiment.status, ExperimentStatus.DRAFT)
        # Check that all the resources were deleted
        self.assertEqual(ResourceModel.select().count(), 0)

        # check recursively all the status
        self._check_process_reset(experiment.protocol_model)
        # Same test with experiment from DB
        self._check_process_reset(ExperimentService.get_experiment_by_id(experiment.id).protocol_model)

    def _check_process_reset(self, process_model: ProcessModel) -> None:
        self.assertEqual(process_model.status, ProcessStatus.DRAFT)
        self.assertTrue(process_model.progress_bar.is_initialized)
        self.assertFalse(process_model.progress_bar.is_running)
        self.assertFalse(process_model.progress_bar.is_finished)
        self.assertIsNone(process_model.error_info)

        for port in process_model.inputs.ports.values():
            self.assertIsNone(port.resource_model)
            self.assertFalse(port.resource_provided)

        for port in process_model.outputs.ports.values():
            self.assertIsNone(port.resource_model)
            self.assertFalse(port.resource_provided)

        # If this is a protocol, check the sub process
        if isinstance(process_model, ProtocolModel):
            for process in process_model.processes.values():
                self._check_process_reset(process)

    async def test_reset_error(self):
        """ Test that we can't reset an experiment if one of its resource is used by another experiment
        """
        experiment: IExperiment = IExperiment(CreateSimpleRobot)
        await experiment.run()

        # Retrieve the robot
        resource = experiment.get_protocol().get_process('facto').get_output('robot')

        # Create a new experiment that uses the previously generated robot
        experiment2: IExperiment = IExperiment(MoveSimpleRobot)
        experiment2.get_protocol().get_process('source').set_param('resource_id', resource._model_id)
        await experiment2.run()

        with self.assertRaises(ResourceUsedInAnotherExperimentException):
            experiment.reset()

    async def test_protocol_copy(self):

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_type(RobotWorldTravelProto)

        await ExperimentRunService.run_experiment(experiment)

        protocol_count = ProtocolModel.select().count()
        task_model = TaskModel.select().count()
        resource_count = ResourceModel.select().count()

        experiment_copy = ExperimentService.clone_experiment(experiment.id)

        self.assertEqual(ProtocolModel.select().count(), protocol_count * 2)
        self.assertEqual(TaskModel.select().count(), task_model * 2)
        self.assertEqual(ResourceModel.select().count(), resource_count)

        await ExperimentRunService.run_experiment(experiment_copy)
        self.assertEqual(ResourceModel.select().count(), resource_count * 2)

    async def test_delete(self):
        experiment: Experiment = ExperimentService.create_experiment_from_protocol_type(RobotWorldTravelProto)

        experiment = await ExperimentRunService.run_experiment(experiment=experiment)

        experiment.delete_instance()

        self.assertEqual(Experiment.select().count(), 0)
        # Check that all the resources were deleted
        self.assertEqual(ResourceModel.select().count(), 0)
        self.assertEqual(ProtocolModel.select().count(), 0)
        self.assertEqual(TaskModel.select().count(), 0)
