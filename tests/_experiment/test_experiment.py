# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from typing import List

from gws_core import (BaseTestCase, Experiment, ExperimentDTO,
                      ExperimentService, ExperimentStatus, GTest, ProcessModel,
                      ProtocolModel, ResourceModel, Robot, RobotService,
                      RobotWorldTravelProto, TaskModel)
from gws_core.experiment.experiment_exception import \
    ResourceUsedInAnotherExperimentException
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_run_service import ExperimentRunService
from gws_core.impl.robot.robot_protocol import (CreateSimpleRobot,
                                                MoveSimpleRobot,
                                                RobotSimpleTravel)
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.io.io_spec import IOSpec
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.process.process_types import ProcessStatus
from gws_core.project.project import Project
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.task.plug import Sink


# test_experiment
class TestExperiment(BaseTestCase):

    def test_create_empty(self):

        project: Project = Project(title="Project")
        project.save()
        experiment_dto: ExperimentDTO = ExperimentDTO(
            title="Experiment title", project_id=project.id)
        experiment = ExperimentService.create_experiment_from_dto(
            experiment_dto)

        self.assertIsNotNone(experiment.id)
        self.assertEqual(experiment.title, 'Experiment title')
        self.assertIsNotNone(experiment.protocol_model.id)
        self.assertEqual(experiment.project.id, project.id)

        ExperimentService.update_experiment_description(
            experiment.id, {"test": "ok"})
        experiment = ExperimentService.get_experiment_by_id(experiment.id)
        self.assert_json(experiment.description, {"test": "ok"})

    def test_run(self):
        # test setting the project to the experiment
        project: Project = Project(title="First project")
        project.save()

        experiment_count = Experiment.select().count()
        task_count = TaskModel.select().count()
        resource_count = ResourceModel.select().count()

        self.assertEqual(Experiment.count_running_or_queued_experiments(), 0)

        # Create experiment 1
        proto1: ProtocolModel = RobotService.create_robot_simple_travel()

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=proto1, title="My exp title", project=project)

        self.assertEqual(Experiment.select().count(), experiment_count + 1)

        # Refresh experiment to be sure it was saved
        experiment = Experiment.get_by_id_and_check(experiment.id)

        self.assertEqual(Experiment.select().count(), experiment_count + 1)
        self.assertEqual(len(experiment.task_models),
                         RobotSimpleTravel.tasks_count)
        self.assertEqual(TaskModel.select().count(),
                         task_count + RobotSimpleTravel.tasks_count)
        self.assertEqual(ResourceModel.select().count(), resource_count)
        self.assertEqual(experiment.title, "My exp title")

        print("Run experiment_2 ...")
        experiment = ExperimentRunService.run_experiment(
            experiment=experiment)

        self.assertEqual(experiment.status, ExperimentStatus.SUCCESS)
        # check that the lab config was saved in the experiment
        self.assertEqual(experiment.lab_config.id, LabConfigModel.id)

        self.assertEqual(ResourceModel.select().count(),
                         resource_count + RobotSimpleTravel.resources_count)
        self.assertEqual(len(experiment.resources),
                         RobotSimpleTravel.resources_count)
        self.assertEqual(ResourceModel.get_by_experiment(
            experiment.id).count(), RobotSimpleTravel.resources_count)
        self.assertIsNone(experiment.pid)

        # refresh experiment
        experiment = Experiment.get_by_id_and_check(
            experiment.id)

        # Test the configuration on fly_1 process (west 2000)
        move_1: ProcessModel = experiment.protocol_model.get_process('move_1')
        # check that the resource was associated to the project
        robot1_model: ResourceModel = move_1.inputs.get_resource_model('robot')
        self.assertEqual(robot1_model.project.id, project.id)
        robot1: Robot = robot1_model.get_resource()

        robot2: Robot = move_1.outputs.get_resource_model('robot').get_resource()
        self.assertEqual(robot1.position[0], robot2.position[0] + 2000)

        # Check if the port resource spec was correctly loaded
        spec: IOSpec = move_1.inputs.get_port('robot').resource_spec
        self.assertIsInstance(spec, IOSpec)
        self.assertEqual(spec.resource_types, [Robot])

        # Test update the project of the experiment
        project2: Project = Project(title="Second project")
        project2.save()

        ExperimentService.update_experiment_project(experiment.id, project2.id)
        robot1_model = robot1_model.refresh()
        self.assertEqual(robot1_model.project.id, project2.id)

        # Test remove the project
        ExperimentService.update_experiment_project(experiment.id, None)
        robot1_model = robot1_model.refresh()
        self.assertIsNone(robot1_model.project)

    def test_run_through_cli(self):

        proto = RobotService.create_robot_world_travel()
        experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=proto)

        ExperimentRunService.create_cli_process_for_experiment(
            experiment=experiment, user=GTest.user)
        self.assertEqual(experiment.status,
                         ExperimentStatus.WAITING_FOR_CLI_PROCESS)
        self.assertTrue(experiment.pid > 0)

        waiting_count = 0
        experiment: Experiment = Experiment.get_by_id_and_check(
            experiment.id)
        print(experiment.protocol_model)
        while experiment.status != ExperimentStatus.SUCCESS:
            print("Waiting 3 secs the experiment to finish ...")
            time.sleep(3)
            if waiting_count == 10:
                raise Exception("The experiment is not finished")
            experiment = experiment.refresh()  # reload from DB
            waiting_count += 1

        self.assertEqual(Experiment.count_running_or_queued_experiments(), 0)
        experiment = Experiment.get_by_id_and_check(experiment.id)
        self.assertEqual(experiment.status, ExperimentStatus.SUCCESS)
        self.assertIsNone(experiment.pid)
        self.assertEqual(experiment.lab_config.id, LabConfigModel.id)

        self.assertEqual(len(experiment.resources),
                         RobotWorldTravelProto.resource_count)

        print("Archive experiment ...")
        self._archive_experiment(experiment, True)

        print("Unarchive experiment ...")
        self._archive_experiment(experiment, False)

        print("Archive experiment again...")
        self._archive_experiment(experiment, True)

    def _archive_experiment(self, experiment: Experiment, archive: bool) -> None:
        result = experiment.archive(archive)
        self.assertTrue(result)

        # check that the resources are archived
        resources: List[ResourceModel] = experiment.resources
        self.assertEqual(len(resources), RobotWorldTravelProto.resource_count)
        for resource in resources:
            self.assertEqual(resource.is_archived, archive)

        # check that the process are archived
        processes: List[ProcessModel] = experiment.task_models
        self.assertEqual(len(processes), RobotWorldTravelProto.tasks_count)
        for process in processes:
            self.assertEqual(process.is_archived, archive)
            self.assertEqual(process.config.is_archived, archive)

    def test_reset(self):

        resource_count = ResourceModel.select().count()
        experiment: Experiment = ExperimentService.create_experiment_from_protocol_type(
            RobotWorldTravelProto)

        experiment = ExperimentRunService.run_experiment(experiment=experiment)

        experiment.reset()

        self.assertEqual(experiment.status, ExperimentStatus.DRAFT)
        # Check that all the resources were deleted
        self.assertEqual(ResourceModel.select().count(), resource_count)

        # check recursively all the status
        self._check_process_reset(experiment.protocol_model)
        # Same test with experiment from DB
        self._check_process_reset(
            ExperimentService.get_experiment_by_id(experiment.id).protocol_model)

    def _check_process_reset(self, process_model: ProcessModel) -> None:
        self.assertEqual(process_model.status, ProcessStatus.DRAFT)
        self.assertFalse(process_model.progress_bar.is_started)
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

    def test_reset_error(self):
        """ Test that we can't reset an experiment if one of its resource is used by another experiment
        """
        experiment: IExperiment = IExperiment(CreateSimpleRobot)
        experiment.run()

        # Retrieve the robot
        resource = experiment.get_protocol().get_process('facto').get_output('robot')

        # Create a new experiment that uses the previously generated robot
        experiment2: IExperiment = IExperiment(MoveSimpleRobot)
        experiment2.get_protocol().get_process(
            'source').set_param('resource_id', resource._model_id)
        experiment2.run()

        with self.assertRaises(ResourceUsedInAnotherExperimentException):
            experiment.reset()

    def test_protocol_copy(self):

        count_protocol = ProtocolModel.select().count()
        count_task = TaskModel.select().count()
        count_resource = ResourceModel.select().count()

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_type(
            RobotWorldTravelProto)

        ExperimentRunService.run_experiment(experiment)

        added_protocol = count_protocol - ProtocolModel.select().count()
        added_task = count_task - TaskModel.select().count()
        added_resource = count_resource - ResourceModel.select().count()

        experiment_copy = ExperimentService.clone_experiment(experiment.id)

        self.assertEqual(ProtocolModel.select().count(),
                         count_protocol - (added_protocol * 2))
        self.assertEqual(TaskModel.select().count(),
                         count_task - (added_task * 2))
        # resources are not copied
        self.assertEqual(ResourceModel.select().count(),
                         count_resource - added_resource)

        ExperimentRunService.run_experiment(experiment_copy)
        self.assertEqual(ResourceModel.select().count(),
                         count_resource - (added_resource * 2))

    def test_delete(self):

        count_experiment = Experiment.select().count()
        count_protocol = ProtocolModel.select().count()
        count_task = TaskModel.select().count()
        count_resource = ResourceModel.select().count()

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_type(
            RobotWorldTravelProto)

        experiment = ExperimentRunService.run_experiment(experiment=experiment)

        experiment.delete_instance()

        self.assertEqual(Experiment.select().count(), count_experiment)
        # Check that all the resources were deleted
        self.assertEqual(ResourceModel.select().count(), count_resource)
        self.assertEqual(ProtocolModel.select().count(), count_protocol)
        self.assertEqual(TaskModel.select().count(), count_task)

    def test_get_by_input_resource(self):

        experiment = IExperiment()
        protocol = experiment.get_protocol()
        i_create = protocol.add_process(RobotCreate, 'create', {})
        sink = protocol.add_sink('sink', i_create >> 'robot')
        experiment.run()

        # generate a resource
        robot_model = sink.refresh().get_input_resource_model(Sink.input_name)

        # create an experiment that uses this resource
        experiment_2 = IExperiment()
        protocol_2 = experiment_2.get_protocol()
        i_move = protocol_2.add_process(RobotMove, 'move', {})
        i_move_2 = protocol_2.add_process(RobotMove, 'move2', {})
        protocol_2.add_source('source', robot_model.id, i_move << 'robot')
        protocol_2.add_source('source_2', robot_model.id, i_move_2 << 'robot')
        experiment_2.run()

        # retrieve the experiments that uses this experiment
        paginator = ExperimentService.get_by_input_resource(robot_model.id)

        # check result
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, experiment_2._experiment.id)

    def test_start_and_stop(self):
        experiment = ExperimentService.create_experiment()

        main_protocol: ProtocolModel = experiment.protocol_model

        create_process: TaskModel = ProtocolService.add_process_to_protocol(
            main_protocol, RobotCreate).process

        # first run
        experiment = ExperimentRunService.run_experiment(experiment)
        create_process = create_process.refresh()

        self.assertEqual(experiment.status, ExperimentStatus.SUCCESS)
        # retrieve resource to compare it after
        created_robot = create_process.out_port('robot').resource_model
        self.assertIsNotNone(created_robot)

        # add a move process to the protocol
        main_protocol = main_protocol.refresh()
        move_process: TaskModel = ProtocolService.add_process_to_protocol(
            main_protocol, RobotMove).process
        ProtocolService.add_connector_to_protocol(main_protocol, create_process.instance_name,
                                                  'robot', move_process.instance_name, 'robot')

        # Check process and protocol status
        create_process = create_process.refresh()
        self.assertEqual(create_process.status, ProcessStatus.SUCCESS)
        main_protocol = main_protocol.refresh()
        self.assertEqual(main_protocol.status, ProcessStatus.PARTIALLY_RUN)

        # Re-run experiment with new process
        experiment = ExperimentRunService.run_experiment(experiment.refresh())
        self.assertEqual(experiment.status, ExperimentStatus.SUCCESS)

        # Check that the create process was not re-run by comparing output
        create_process = create_process.refresh()
        created_robot_2 = create_process.out_port('robot').resource_model
        self.assertEqual(created_robot.id, created_robot_2.id)

        # Check that the move process was run
        move_process = move_process.refresh()
        self.assertEqual(move_process.status, ProcessStatus.SUCCESS)
