

import time
from typing import List

from gws_core import (BaseTestCase, ProcessModel, ProtocolModel, ResourceModel,
                      Scenario, ScenarioSaveDTO, ScenarioService,
                      ScenarioStatus, TaskModel)
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.robot.robot_protocol import (RobotSimpleTravel,
                                                RobotWorldTravelProto)
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_service import RobotService
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.io.io_spec import IOSpec
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.process.process_types import ProcessStatus
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.task.plug import Sink
from gws_core.test.gtest import GTest


# test_scenario
class TestScenario(BaseTestCase):

    def test_create_empty(self):

        folder = SpaceFolder(title="Froject")
        folder.save()
        scenario_dto = ScenarioSaveDTO(title="Scenario title", folder_id=folder.id)
        scenario = ScenarioService.create_scenario_from_dto(
            scenario_dto)

        self.assertIsNotNone(scenario.id)
        self.assertEqual(scenario.title, 'Scenario title')
        self.assertIsNotNone(scenario.protocol_model.id)
        self.assertEqual(scenario.folder.id, folder.id)

        ScenarioService.update_scenario_description(
            scenario.id, {"test": "ok"})
        scenario = ScenarioService.get_by_id_and_check(scenario.id)
        self.assert_json(scenario.description, {"test": "ok"})

    def test_run(self):
        # test setting the folder to the scenario
        folder = SpaceFolder(title="First folder")
        folder.save()

        scenario_count = Scenario.select().count()
        task_count = TaskModel.select().count()
        resource_count = ResourceModel.select().count()

        self.assertEqual(Scenario.count_running_or_queued_scenarios(), 0)

        # Create scenario 1
        proto1 = RobotService.create_robot_simple_travel()

        scenario = ScenarioService.create_scenario_from_protocol_model(
            protocol_model=proto1, title="My exp title", folder=folder)

        self.assertEqual(Scenario.select().count(), scenario_count + 1)

        # Refresh scenario to be sure it was saved
        scenario = Scenario.get_by_id_and_check(scenario.id)

        self.assertEqual(Scenario.select().count(), scenario_count + 1)
        self.assertEqual(len(scenario.task_models),
                         RobotSimpleTravel.tasks_count)
        self.assertEqual(TaskModel.select().count(),
                         task_count + RobotSimpleTravel.tasks_count)
        self.assertEqual(ResourceModel.select().count(), resource_count)
        self.assertEqual(scenario.title, "My exp title")

        print("Run scenario_2 ...")
        scenario = ScenarioRunService.run_scenario(
            scenario=scenario)

        self.assertEqual(scenario.status, ScenarioStatus.SUCCESS)
        # check that the lab config was saved in the scenario
        self.assertEqual(scenario.lab_config.id, LabConfigModel.id)

        self.assertEqual(ResourceModel.select().count(),
                         resource_count + RobotSimpleTravel.resources_count)
        self.assertEqual(len(scenario.resources),
                         RobotSimpleTravel.resources_count)
        self.assertEqual(ResourceModel.get_by_scenario(
            scenario.id).count(), RobotSimpleTravel.resources_count)
        self.assertIsNone(scenario.pid)

        # refresh scenario
        scenario: Scenario = Scenario.get_by_id_and_check(scenario.id)

        # Test the configuration on fly_1 process (west 2000)
        move_1 = scenario.protocol_model.get_process('move_1')
        # check that the resource was associated to the folder
        robot1_model = move_1.inputs.get_resource_model('robot')
        self.assertEqual(robot1_model.folder.id, folder.id)
        robot1: Robot = robot1_model.get_resource()

        robot2: Robot = move_1.outputs.get_resource_model('robot').get_resource()
        self.assertEqual(robot1.position[0], robot2.position[0] + 2000)

        # Check if the port resource spec was correctly loaded
        spec: IOSpec = move_1.inputs.get_port('robot').resource_spec
        self.assertIsInstance(spec, IOSpec)
        self.assertEqual(spec.resource_types, [Robot])

        # Test update the folder of the scenario
        folder2 = SpaceFolder(title="Second folder")
        folder2.save()

        ScenarioService.update_scenario_folder(scenario.id, folder2.id)
        robot1_model = robot1_model.refresh()
        self.assertEqual(robot1_model.folder.id, folder2.id)

        # Test remove the folder
        ScenarioService.update_scenario_folder(scenario.id, None)
        robot1_model = robot1_model.refresh()
        self.assertIsNone(robot1_model.folder)

    def test_run_through_cli(self):

        proto = RobotService.create_robot_world_travel()
        scenario = ScenarioService.create_scenario_from_protocol_model(
            protocol_model=proto)

        ScenarioRunService.create_cli_for_scenario(
            scenario=scenario, user=GTest.user)
        self.assertEqual(scenario.status,
                         ScenarioStatus.WAITING_FOR_CLI_PROCESS)
        self.assertTrue(scenario.pid > 0)

        waiting_count = 0
        scenario: Scenario = Scenario.get_by_id_and_check(
            scenario.id)
        print(scenario.protocol_model)
        while scenario.status != ScenarioStatus.SUCCESS:
            print("Waiting 3 secs the scenario to finish ...")
            time.sleep(3)
            if waiting_count == 10:
                raise Exception("The scenario is not finished")
            scenario = scenario.refresh()  # reload from DB
            waiting_count += 1

        self.assertEqual(Scenario.count_running_or_queued_scenarios(), 0)
        scenario = Scenario.get_by_id_and_check(scenario.id)
        self.assertEqual(scenario.status, ScenarioStatus.SUCCESS)
        self.assertIsNone(scenario.pid)
        self.assertEqual(scenario.lab_config.id, LabConfigModel.id)

        self.assertEqual(len(scenario.resources),
                         RobotWorldTravelProto.resource_count)

        print("Archive scenario ...")
        self._archive_scenario(scenario, True)

        print("Unarchive scenario ...")
        self._archive_scenario(scenario, False)

        print("Archive scenario again...")
        self._archive_scenario(scenario, True)

    def _archive_scenario(self, scenario: Scenario, archive: bool) -> None:
        result = scenario.archive(archive)
        self.assertTrue(result)

        # check that the resources are archived
        resources: List[ResourceModel] = scenario.resources
        self.assertEqual(len(resources), RobotWorldTravelProto.resource_count)
        for resource in resources:
            self.assertEqual(resource.is_archived, archive)

        # check that the process are archived
        processes: List[ProcessModel] = scenario.task_models
        self.assertEqual(len(processes), RobotWorldTravelProto.tasks_count)
        for process in processes:
            self.assertEqual(process.is_archived, archive)

    def test_reset(self):

        resource_count = ResourceModel.select().count()
        scenario: Scenario = ScenarioService.create_scenario_from_protocol_type(
            RobotWorldTravelProto)

        scenario = ScenarioRunService.run_scenario(scenario=scenario)

        scenario.reset()

        self.assertEqual(scenario.status, ScenarioStatus.DRAFT)
        # Check that all the resources were deleted
        self.assertEqual(ResourceModel.select().count(), resource_count)

        # check recursively all the status
        self._check_process_reset(scenario.protocol_model)
        # Same test with scenario from DB
        self._check_process_reset(
            ScenarioService.get_by_id_and_check(scenario.id).protocol_model)

        # test get scenario protocol config
        result = scenario.export_protocol()
        self.assertIsNotNone(result)

    def _check_process_reset(self, process_model: ProcessModel) -> None:
        self.assertEqual(process_model.status, ProcessStatus.DRAFT)
        self.assertFalse(process_model.progress_bar.is_started)
        self.assertFalse(process_model.progress_bar.is_running)
        self.assertFalse(process_model.progress_bar.is_finished)
        self.assertIsNone(process_model.get_error_info())

        for port in process_model.inputs.ports.values():
            self.assertIsNone(port.get_resource_model())
            self.assertFalse(port.resource_provided)

        for port in process_model.outputs.ports.values():
            self.assertIsNone(port.get_resource_model())
            self.assertFalse(port.resource_provided)

        # If this is a protocol, check the sub process
        if isinstance(process_model, ProtocolModel):
            for process in process_model.processes.values():
                self._check_process_reset(process)

    def test_protocol_copy(self):

        count_protocol = ProtocolModel.select().count()
        count_task = TaskModel.select().count()
        count_resource = ResourceModel.select().count()

        scenario: Scenario = ScenarioService.create_scenario_from_protocol_type(
            RobotWorldTravelProto)

        ScenarioRunService.run_scenario(scenario)

        added_protocol = count_protocol - ProtocolModel.select().count()
        added_task = count_task - TaskModel.select().count()
        added_resource = count_resource - ResourceModel.select().count()

        scenario_copy = ScenarioService.clone_scenario(scenario.id)

        self.assertEqual(ProtocolModel.select().count(),
                         count_protocol - (added_protocol * 2))
        self.assertEqual(TaskModel.select().count(),
                         count_task - (added_task * 2))
        # resources are not copied
        self.assertEqual(ResourceModel.select().count(),
                         count_resource - added_resource)

        ScenarioRunService.run_scenario(scenario_copy)
        self.assertEqual(ResourceModel.select().count(),
                         count_resource - (added_resource * 2))

    def test_delete(self):

        count_scenario = Scenario.select().count()
        count_protocol = ProtocolModel.select().count()
        count_task = TaskModel.select().count()
        count_resource = ResourceModel.select().count()

        scenario: Scenario = ScenarioService.create_scenario_from_protocol_type(
            RobotWorldTravelProto)

        scenario = ScenarioRunService.run_scenario(scenario=scenario)

        scenario.delete_instance()

        self.assertEqual(Scenario.select().count(), count_scenario)
        # Check that all the resources were deleted
        self.assertEqual(ResourceModel.select().count(), count_resource)
        self.assertEqual(ProtocolModel.select().count(), count_protocol)
        self.assertEqual(TaskModel.select().count(), count_task)

    def test_get_by_input_resource(self):

        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        i_create = protocol.add_process(RobotCreate, 'create', {})
        sink = protocol.add_sink('sink', i_create >> 'robot')
        scenario.run()

        # generate a resource
        robot_model = sink.refresh().get_input_resource_model(Sink.input_name)

        # create an scenario that uses this resource
        scenario_2 = ScenarioProxy()
        protocol_2 = scenario_2.get_protocol()
        i_move = protocol_2.add_process(RobotMove, 'move', {})
        i_move_2 = protocol_2.add_process(RobotMove, 'move2', {})
        protocol_2.add_source('source', robot_model.id, i_move << 'robot')
        protocol_2.add_source('source_2', robot_model.id, i_move_2 << 'robot')
        scenario_2.run()

        # retrieve the scenarios that uses this scenario
        paginator = ScenarioService.get_next_scenarios_of_resource(robot_model.id)

        # check result
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, scenario_2._scenario.id)

    def test_start_and_stop(self):
        scenario = ScenarioService.create_scenario()

        main_protocol: ProtocolModel = scenario.protocol_model

        create_process: TaskModel = ProtocolService.add_process_to_protocol(
            main_protocol, RobotCreate).process

        # first run
        scenario = ScenarioRunService.run_scenario(scenario)
        create_process = create_process.refresh()

        self.assertEqual(scenario.status, ScenarioStatus.SUCCESS)
        # retrieve resource to compare it after
        created_robot = create_process.out_port('robot').get_resource_model()
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

        # Re-run scenario with new process
        scenario = ScenarioRunService.run_scenario(scenario.refresh())
        self.assertEqual(scenario.status, ScenarioStatus.SUCCESS)

        # Check that the create process was not re-run by comparing output
        create_process = create_process.refresh()
        created_robot_2 = create_process.out_port('robot').get_resource_model()
        self.assertEqual(created_robot.id, created_robot_2.id)

        # Check that the move process was run
        move_process = move_process.refresh()
        self.assertEqual(move_process.status, ProcessStatus.SUCCESS)

    def test_delete_intermediate_resources(self):

        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        i_create = protocol.add_process(RobotCreate, 'create')
        move_1 = protocol.add_process(RobotMove, 'move_1')
        move_2 = protocol.add_process(RobotMove, 'move_2')
        protocol.add_connector(i_create >> 'robot', move_1 << 'robot')
        protocol.add_connector(move_1 >> 'robot', move_2 << 'robot')
        sink = protocol.add_sink('sink', move_2 >> 'robot')
        scenario.run()

        # flag the output of i_create
        create_output = i_create.refresh().get_output_resource_model('robot')
        create_output.flagged = True
        create_output.save()

        # Delete the intermediate resource data
        ScenarioService.delete_intermediate_resources(scenario.get_model().id)

        create_output.refresh()
        # the output of i_create should not be deleted because it is flagged
        self.assertFalse(create_output.content_is_deleted)
        # the output of move_2 should not be deleted because it is the output of the scenario
        self.assertFalse(move_2.refresh().get_output_resource_model('robot').content_is_deleted)
        # the output of move_1 should be deleted
        self.assertTrue(move_1.refresh().get_output_resource_model('robot').content_is_deleted)
