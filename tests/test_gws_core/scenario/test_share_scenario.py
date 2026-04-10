from datetime import timedelta
from typing import cast
from unittest import TestCase

from gws_core import (
    ConfigParams,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    Task,
    TaskInputs,
    TaskOutputs,
    task_decorator,
)
import os
import tarfile

from gws_core.core.utils.date_helper import DateHelper
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotMove
from gws_core.lab.lab_model.lab_model import LabModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.impl.file.file import File
from gws_core.resource.resource_zipper import ResourceZipper
from gws_core.scenario.scenario_archive_zipper import ScenarioArchiveZipper
from gws_core.scenario.task.scenario_archive_zipper_task import ScenarioArchiveZipperTask
from gws_core.scenario.task.scenario_loader_from_archive import ScenarioLoaderFromArchive
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_builder import ScenarioBuilder
from gws_core.scenario.scenario_enums import ScenarioCreationType, ScenarioStatus
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.scenario.scenario_transfert_service import ScenarioTransfertService
from gws_core.scenario.task.scenario_downloader_share_link import ScenarioDownloaderShareLink
from gws_core.scenario.task.send_scenario_to_lab import SendScenarioToLab
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_dto import (
    GenerateShareLinkDTO,
    ShareEntityCreateMode,
    ShareLinkEntityType,
    ShareLinkType,
)
from gws_core.share.shared_resource import SharedResource
from gws_core.share.shared_scenario import SharedScenario
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigins
from gws_core.tag.tag_dto import TagOriginType
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.task.plug.input_task import InputTask
from gws_core.task.plug.output_task import OutputTask
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case import BaseTestCase
from gws_core.test.test_helper import TestHelper
from gws_core.test.test_start_unvicorn_app import TestStartUvicornApp
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(unique_name="RobotsGeneratorShare")
class RobotsGeneratorShare(Task):
    input_specs: InputSpecs = InputSpecs({"robot": InputSpec(Robot)})
    output_specs: OutputSpecs = OutputSpecs({"set": OutputSpec(ResourceSet)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        robot_1 = inputs.get("robot")
        robot_2 = Robot.empty()
        robot_2.age = 99
        robot_2.name = "Robot 2"

        resource_set: ResourceSet = ResourceSet()
        # Add the input robot that was already created and saved
        resource_set.add_resource(robot_1, unique_name="Robot 1", create_new_resource=False)
        resource_set.add_resource(robot_2)
        return {"set": resource_set}


class ShareScenarioTestSetup:
    """Builds and runs the standard share-scenario test topology (source→move→generate→output),
    then exports the scenario package so tests can use it directly without any HTTP calls.

    Attributes
    ----------
    input_robot_model : ResourceModel
        The robot resource used as the scenario input.
    folder : SpaceFolder
        The folder the scenario is placed in.
    scenario_model : Scenario
        The Scenario DB model after the run.
    protocol_model : ProtocolModel
        The protocol DB model after the run.
    tag_key : str
        Tag key applied to the scenario.
    tag_value : str
        Tag value applied to the scenario.
    """

    initial_input_robot_model: ResourceModel
    initial_folder: SpaceFolder
    initial_scenario_model: Scenario
    initial_protocol_model: ProtocolModel

    initial_tag_key: str
    initial_tag_value: str

    create_mode: ShareEntityCreateMode
    _tc: TestCase

    def __init__(
        self,
        test_case: TestCase,
        title: str,
        tag_key: str,
        tag_value: str,
        create_mode: ShareEntityCreateMode = ShareEntityCreateMode.NEW_ID,
    ) -> None:
        self._tc = test_case
        self.initial_tag_key = tag_key
        self.initial_tag_value = tag_value
        self.create_mode = create_mode

        self.initial_input_robot_model = TestHelper.save_robot_resource()
        self.initial_folder = TestHelper.create_default_folder()

        scenario = ScenarioProxy(title=title, folder=self.initial_folder)
        scenario.add_tag(
            Tag(
                tag_key,
                tag_value,
                is_propagable=True,
                origins=TagOrigins(TagOriginType.USER, "test"),
            )
        )
        protocol = scenario.get_protocol()
        move = protocol.add_process(RobotMove, "move", config_params={"moving_step": 100})
        generate = protocol.add_process(RobotsGeneratorShare, "generate")
        protocol.add_resource("source", self.initial_input_robot_model.id, move << "robot")
        protocol.add_connector(move >> "robot", generate << "robot")
        protocol.add_output("output", generate >> "set")
        scenario.run()

        self.initial_scenario_model = scenario.refresh().get_model()
        self.initial_protocol_model = protocol.refresh().get_model()

        # load the progress bar so if the element are deleted in DB, progress_bar still exist
        self._tc.assertIsNotNone(self.initial_protocol_model.progress_bar)
        self._tc.assertIsNotNone(self.get_initial_move_process().progress_bar)

    def get_initial_move_process(self) -> TaskModel:
        return cast(TaskModel, self.initial_protocol_model.get_process("move"))

    def get_initial_source_process(self) -> TaskModel:
        return cast(TaskModel, self.initial_protocol_model.get_process("source"))

    def get_initial_generate_process(self) -> TaskModel:
        return cast(TaskModel, self.initial_protocol_model.get_process("generate"))

    def get_initial_output_process(self) -> TaskModel:
        return cast(TaskModel, self.initial_protocol_model.get_process("output"))

    def get_initial_source_resource(self) -> ResourceModel:
        return (
            self.get_initial_source_process().out_port(InputTask.output_name).get_resource_model()
        )

    def get_initial_move_resource(self) -> ResourceModel:
        return self.get_initial_move_process().out_port("robot").get_resource_model()

    def get_initial_resource_set(self) -> ResourceModel:
        return self.get_initial_generate_process().out_port("set").get_resource_model()

    def _check_id(self, imported_id: str, original_id: str) -> None:
        """Assert that imported_id equals or differs from original_id depending on create_mode."""
        if self.create_mode == ShareEntityCreateMode.KEEP_ID:
            self._tc.assertEqual(imported_id, original_id)
        else:
            self._tc.assertNotEqual(imported_id, original_id)

    def assert_imported_scenario(
        self,
        new_scenario: Scenario,
        new_protocol_model: ProtocolModel,
        new_source: TaskModel,
        new_move: TaskModel,
    ) -> None:
        self._check_id(new_scenario.id, self.initial_scenario_model.id)
        self._tc.assertEqual(new_scenario.title, self.initial_scenario_model.title)
        self._tc.assertEqual(new_scenario.folder.id, self.initial_folder.id)
        self._tc.assertEqual(new_scenario.status, self.initial_scenario_model.status)
        self._tc.assertEqual(new_scenario.creation_type, ScenarioCreationType.IMPORTED)

        # Check the tags
        tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, new_scenario.id)
        self._tc.assertEqual(len(tags.get_tags()), 1)
        tag = tags.get_tags()[0]
        self._tc.assertEqual(tag.tag_key, self.initial_tag_key)
        self._tc.assertEqual(tag.tag_value, self.initial_tag_value)
        self._tc.assertTrue(tag.is_propagable)
        origins = tag.get_origins()
        self._tc.assertEqual(origins.count_origins(), 1)
        self._tc.assertTrue(origins.has_origin(TagOriginType.USER, "test"))

        # Check the protocol and processes
        self._assert_imported_protocol(new_protocol_model, new_source, new_move)

        # Check the resources
        self._assert_imported_resources(new_scenario, new_protocol_model, new_source, new_move)

    def _assert_imported_protocol(
        self,
        new_protocol_model: ProtocolModel,
        new_source: TaskModel,
        new_move: TaskModel,
    ) -> None:
        self._check_id(new_protocol_model.id, self.initial_protocol_model.id)
        self._tc.assertEqual(len(new_protocol_model.processes), 4)
        self._tc.assertEqual(len(new_protocol_model.connectors), 3)
        self._tc.assertEqual(new_protocol_model.status, self.initial_protocol_model.status)
        self._tc.assertEqual(
            new_protocol_model.progress_bar.get_elapsed_time(),
            self.initial_protocol_model.progress_bar.get_elapsed_time(),
        )

        # Check process IDs
        self._check_id(new_source.id, self.get_initial_source_process().id)
        self._check_id(new_move.id, self.get_initial_move_process().id)
        self._check_id(
            new_protocol_model.get_process("generate").id,
            self.get_initial_generate_process().id,
        )
        self._check_id(
            new_protocol_model.get_process("output").id,
            self.get_initial_output_process().id,
        )

        self._tc.assertEqual(
            new_source.process_typing_name,
            self.get_initial_source_process().process_typing_name,
        )
        self._tc.assertEqual(
            new_move.process_typing_name, self.get_initial_move_process().process_typing_name
        )
        self._tc.assertEqual(new_move.status, self.get_initial_move_process().status)
        self._tc.assertEqual(
            new_move.progress_bar.get_elapsed_time(),
            self.get_initial_move_process().progress_bar.get_elapsed_time(),
        )
        self._tc.assertEqual(
            new_protocol_model.get_process("generate").process_typing_name,
            self.get_initial_generate_process().process_typing_name,
        )
        self._tc.assertEqual(
            new_protocol_model.get_process("output").process_typing_name,
            self.get_initial_output_process().process_typing_name,
        )

    def _assert_imported_resources(
        self,
        new_scenario: Scenario,
        new_protocol_model: ProtocolModel,
        new_source: TaskModel,
        new_move: TaskModel,
        output_only: bool = False,
    ) -> None:
        # Check the source resource
        new_source_output = new_source.out_port(InputTask.output_name).get_resource_model()
        self._tc.assertIsNotNone(new_source_output)
        self._check_id(new_source_output.id, self.get_initial_source_resource().id)
        self._tc.assertIsNone(new_source_output.scenario)
        self._tc.assertEqual(new_source_output.origin, ResourceOrigin.IMPORTED_FROM_LAB)
        self._tc.assertTrue(new_source_output.flagged)
        self._tc.assertEqual(new_source.source_config_id, new_source_output.id)
        self._tc.assertEqual(
            new_source.config.get_value(InputTask.config_name), new_source_output.id
        )

        new_move_process = new_protocol_model.get_process("move")
        self._tc.assertEqual(
            new_move_process.in_port("robot").get_resource_model_id(), new_source_output.id
        )
        new_move_resource_1 = new_move_process.out_port("robot").get_resource_model()
        initial_resource_1 = self.get_initial_move_resource()
        self._tc.assertIsNotNone(new_move_resource_1)
        self._check_id(new_move_resource_1.id, initial_resource_1.id)
        self._tc.assertEqual(new_move_resource_1.scenario.id, new_scenario.id)
        self._tc.assertEqual(new_move_resource_1.origin, ResourceOrigin.IMPORTED_FROM_LAB)
        self._tc.assertEqual(
            new_move_resource_1.task_model.id, new_protocol_model.get_process("move").id
        )
        self._tc.assertEqual(new_move_resource_1.folder.id, new_scenario.folder.id)
        self._tc.assertFalse(new_move_resource_1.flagged)
        self._tc.assertEqual(
            new_move_resource_1.resource_typing_name, initial_resource_1.resource_typing_name
        )
        # Check TaskInputModel
        self._tc.assertTrue(
            TaskInputModel.select()
            .where(
                (TaskInputModel.scenario == new_scenario.id)
                & (TaskInputModel.task_model == new_move_process.id)
                & (TaskInputModel.port_name == "robot")
                & (TaskInputModel.resource_model == new_source_output.id)
            )
            .exists()
        )

        # Check the resource set
        initial_resource_set_model = self.get_initial_resource_set()
        new_generator_process = new_protocol_model.get_process("generate")
        new_resource_set_model = new_generator_process.out_port("set").get_resource_model()
        self._tc.assertIsNotNone(new_resource_set_model)
        self._check_id(new_resource_set_model.id, initial_resource_set_model.id)
        self._tc.assertTrue(new_resource_set_model.flagged)

        # Retrieve resource content only for the output resource
        new_output_process = new_protocol_model.get_process("output")
        output_resource_set_model = new_output_process.in_port(
            OutputTask.input_name
        ).get_resource_model()
        new_resource_set: ResourceSet = output_resource_set_model.get_resource()
        self._tc.assertIsInstance(new_resource_set, ResourceSet)
        self._tc.assertEqual(len(new_resource_set.get_resources()), 2)

        # Check TaskInputModel
        self._tc.assertTrue(
            TaskInputModel.select()
            .where(
                (TaskInputModel.scenario == new_scenario.id)
                & (TaskInputModel.task_model == new_generator_process.id)
                & (TaskInputModel.port_name == "robot")
                & (TaskInputModel.resource_model == new_move_resource_1.id)
            )
            .exists()
        )

        initial_resource_set = cast(ResourceSet, initial_resource_set_model.get_resource())

        new_robot_1_model = ResourceModel.get_by_id_and_check(
            new_resource_set.get_resource("Robot 1").get_model_id()
        )
        self._check_id(
            new_robot_1_model.id, initial_resource_set.get_resource("Robot 1").get_model_id()
        )
        # verify that the robot 1 is the output of the move
        self._tc.assertEqual(
            new_robot_1_model.id, new_move.out_port("robot").get_resource_model().id
        )
        self._tc.assertEqual(new_robot_1_model.scenario.id, new_scenario.id)
        self._tc.assertEqual(new_robot_1_model.task_model.id, new_move.get_id())
        self._tc.assertEqual(new_robot_1_model.generated_by_port_name, "robot")
        # The first robot should not be associated directly with resource set because it is created before
        self._tc.assertIsNone(new_robot_1_model.parent_resource_id)

        new_robot_2_model = ResourceModel.get_by_id_and_check(
            new_resource_set.get_resource("Robot 2").get_model_id()
        )
        self._check_id(
            new_robot_2_model.id, initial_resource_set.get_resource("Robot 2").get_model_id()
        )
        self._tc.assertEqual(new_robot_2_model.parent_resource_id, new_resource_set_model.id)
        self._tc.assertEqual(new_robot_2_model.scenario.id, new_scenario.id)
        self._tc.assertEqual(new_robot_2_model.task_model.id, new_generator_process.id)
        self._tc.assertEqual(new_robot_2_model.generated_by_port_name, "set")

        self._tc.assertEqual(TaskInputModel.get_by_scenario(new_scenario.id).count(), 3)

        if not output_only:
            self._assert_imported_shared_resources(
                new_scenario,
                new_source_output,
                new_move_resource_1,
                new_resource_set_model,
                initial_resource_set_model,
                initial_resource_set,
                new_robot_1_model,
                new_robot_2_model,
            )
        self._tc.assertTrue(
            TaskInputModel.select()
            .where(
                (TaskInputModel.scenario == new_scenario.id)
                & (TaskInputModel.task_model == new_output_process.id)
                & (TaskInputModel.port_name == OutputTask.input_name)
                & (TaskInputModel.resource_model == new_resource_set_model.id)
            )
            .exists()
        )

    def _assert_imported_shared_resources(
        self,
        new_scenario: Scenario,
        new_source_output: ResourceModel,
        new_move_resource_1: ResourceModel,
        new_resource_set_model: ResourceModel,
        initial_resource_set_model: ResourceModel,
        initial_resource_set: ResourceSet,
        new_robot_1_model: ResourceModel,
        new_robot_2_model: ResourceModel,
    ) -> None:
        """Check shared scenario and resource entries."""
        # Test shared scenario and resource info
        shared_scenario = SharedScenario.get_and_check_entity_origin(new_scenario.id)
        self._tc.assertIsNotNone(shared_scenario)
        self._tc.assertEqual(shared_scenario.external_id, self.initial_scenario_model.id)

        # Check that all resources have a SharedResource entry with the correct external_id
        shared_resource = SharedResource.get_and_check_entity_origin(new_source_output.id)
        self._tc.assertIsNotNone(shared_resource)
        self._tc.assertEqual(shared_resource.external_id, self.get_initial_source_resource().id)

        shared_resource = SharedResource.get_and_check_entity_origin(new_move_resource_1.id)
        self._tc.assertIsNotNone(shared_resource)
        self._tc.assertEqual(shared_resource.external_id, self.get_initial_move_resource().id)

        shared_resource = SharedResource.get_and_check_entity_origin(new_resource_set_model.id)
        self._tc.assertIsNotNone(shared_resource)
        self._tc.assertEqual(shared_resource.external_id, initial_resource_set_model.id)

        shared_resource = SharedResource.get_and_check_entity_origin(new_robot_1_model.id)
        self._tc.assertIsNotNone(shared_resource)
        self._tc.assertEqual(
            shared_resource.external_id,
            initial_resource_set.get_resource("Robot 1").get_model_id(),
        )

        shared_resource = SharedResource.get_and_check_entity_origin(new_robot_2_model.id)
        self._tc.assertIsNotNone(shared_resource)
        self._tc.assertEqual(
            shared_resource.external_id,
            initial_resource_set.get_resource("Robot 2").get_model_id(),
        )

    def assert_imported_outputs_only(self, new_scenario: Scenario) -> None:
        new_protocol = new_scenario.protocol_model

        # 3 resources should have been created (resource set and 2 robots)
        self._tc.assertEqual(
            ResourceModel.select().where(ResourceModel.scenario == new_scenario.id).count(), 3
        )
        # All TaskInputModel should have been created because even if the source resource is not imported,
        #  the input task config should still be created with a Shell resource
        self._tc.assertEqual(TaskInputModel.get_by_scenario(new_scenario.id).count(), 3)

        # the source task should be configured event if the source resource is not imported
        new_source: TaskModel = new_protocol.get_process("source")
        self._tc.assertIsNotNone(new_source.source_config_id)
        self._tc.assertIsNotNone(new_source.out_port(InputTask.output_name).get_resource_model())

        new_output_process = new_protocol.get_process("output")
        self._tc.assertIsNotNone(
            new_output_process.in_port(OutputTask.input_name).get_resource_model()
        )


# test_share_scenario
class TestShareScenario(BaseTestCase):
    # method to start the uvicorn app only once for all the tests
    # required because ResourceService.upload_resource_from_link needs API
    # and close it after all the tests
    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        cls.start_uvicorn_app = TestStartUvicornApp()
        cls.start_uvicorn_app.enter()

    @classmethod
    def clear_after_test(cls):
        super().clear_after_test()
        cls.start_uvicorn_app.exit(None, None, None)

    def test_share_scenario(self):
        setup = ShareScenarioTestSetup(
            self, "Test scenario", "scenario_tag", "scenario_value", ShareEntityCreateMode.NEW_ID
        )

        share_link = ShareLinkService.generate_share_link(
            GenerateShareLinkDTO(
                entity_id=setup.initial_scenario_model.id,
                entity_type=ShareLinkEntityType.SCENARIO,
                valid_until=DateHelper.now_utc() + timedelta(days=1),
            ),
            ShareLinkType.PUBLIC,
        )

        new_scenario = ScenarioTransfertService.import_from_lab_sync(
            ScenarioDownloaderShareLink.build_config(
                share_link.get_download_link(), "All", "Force new scenario"
            )
        )

        new_protocol_model = new_scenario.protocol_model
        new_source = cast(TaskModel, new_protocol_model.get_process("source"))
        new_move = cast(TaskModel, new_protocol_model.get_process("move"))
        setup.assert_imported_scenario(new_scenario, new_protocol_model, new_source, new_move)

        # Test output only mode
        new_scenario_outputs_only = ScenarioTransfertService.import_from_lab_sync(
            ScenarioDownloaderShareLink.build_config(
                share_link.get_download_link(), "Outputs only", "Force new scenario"
            )
        )
        new_protocol_model_outputs_only = new_scenario_outputs_only.protocol_model
        new_source_outputs_only = cast(
            TaskModel, new_protocol_model_outputs_only.get_process("source")
        )
        new_move_outputs_only = cast(TaskModel, new_protocol_model_outputs_only.get_process("move"))

        setup.assert_imported_scenario(
            new_scenario_outputs_only,
            new_protocol_model_outputs_only,
            new_source_outputs_only,
            new_move_outputs_only,
        )

    def test_keep_id_exists(self):
        """Test ScenarioBuilder with KEEP_ID: deletes the scenario then rebuilds it from a
        locally-exported package and zipped resources, without any HTTP calls."""
        setup = ShareScenarioTestSetup(
            self,
            "Test scenario skip if exists",
            "skip_tag",
            "skip_value",
            ShareEntityCreateMode.KEEP_ID,
        )

        # Export package and zip all resources before deleting the scenario
        scenario_package = ScenarioService.export_scenario(setup.initial_scenario_model.id)
        current_user = CurrentUserService.get_and_check_current_user()
        zip_paths = {}
        for resource_models in scenario_package.main_resource_models:
            zipper = ResourceZipper(current_user)
            zipper.add_resource_model(resource_models.id)
            zipper.close_zip()
            zip_paths[resource_models.id] = zipper.get_zip_file_path()
        origin = ExternalLabApiService.get_current_lab_info(current_user)

        # Delete the scenario and input resource so the builder recreates them from scratch
        ScenarioProxy.from_existing_scenario(setup.initial_scenario_model.id).delete()
        self.assertIsNone(Scenario.get_by_id(setup.initial_scenario_model.id))
        setup.initial_input_robot_model.delete_instance()

        builder = ScenarioBuilder(
            scenario_info=scenario_package,
            origin=origin,
            create_mode=ShareEntityCreateMode.KEEP_ID,
        )
        new_scenario = builder.build()
        builder.fill_zip_resources(zip_paths)

        new_protocol_model = new_scenario.protocol_model
        new_source = cast(TaskModel, new_protocol_model.get_process("source"))
        new_move = cast(TaskModel, new_protocol_model.get_process("move"))
        setup.assert_imported_scenario(new_scenario, new_protocol_model, new_source, new_move)

        # Export the scenario again and zip only the output resource
        output_resource_model = (
            setup.get_initial_output_process().in_port(OutputTask.input_name).get_resource_model()
        )
        output_zip_paths = {}
        zipper = ResourceZipper(current_user)
        zipper.add_resource_model(output_resource_model.id)
        zipper.close_zip()
        output_zip_paths[output_resource_model.id] = zipper.get_zip_file_path()

        # Delete the rebuilt scenario before importing outputs only
        # Leave the input resource to simulate an import where the input resource already exists.
        ScenarioProxy.from_existing_scenario(new_scenario.id).delete()

        builder_outputs = ScenarioBuilder(
            scenario_info=scenario_package,
            origin=origin,
            create_mode=ShareEntityCreateMode.KEEP_ID,
        )
        new_scenario_outputs_only = builder_outputs.build()
        builder_outputs.fill_zip_resources(output_zip_paths)
        new_protocol_model_outputs_only = new_scenario_outputs_only.protocol_model
        new_source_outputs_only = cast(
            TaskModel, new_protocol_model_outputs_only.get_process("source")
        )
        new_move_outputs_only = cast(TaskModel, new_protocol_model_outputs_only.get_process("move"))
        setup.assert_imported_scenario(
            new_scenario_outputs_only,
            new_protocol_model_outputs_only,
            new_source_outputs_only,
            new_move_outputs_only,
        )

        # Step 3: Rebuild with ALL resources without deleting the scenario.
        # KEEP_ID mode should handle the case where the scenario already exists.
        # if should fill the remaining resources
        builder_all_again = ScenarioBuilder(
            scenario_info=scenario_package,
            origin=origin,
            create_mode=ShareEntityCreateMode.KEEP_ID,
        )
        new_scenario_again = builder_all_again.build()
        builder_all_again.fill_zip_resources(zip_paths)

        new_protocol_model_again = new_scenario_again.protocol_model
        new_source_again = cast(TaskModel, new_protocol_model_again.get_process("source"))
        new_move_again = cast(TaskModel, new_protocol_model_again.get_process("move"))
        setup.assert_imported_scenario(
            new_scenario_again, new_protocol_model_again, new_source_again, new_move_again
        )

    def test_send_scenario(self):
        input_robot_model = TestHelper.save_robot_resource()

        # Create and run a scenario
        folder = TestHelper.create_default_folder()
        scenario = ScenarioProxy(title="Test scenario", folder=folder)

        scenario.add_tag(
            Tag(
                "scenario_tag",
                "scenario_value",
                is_propagable=True,
                origins=TagOrigins(TagOriginType.USER, "test"),
            )
        )
        protocol = scenario.get_protocol()

        move = protocol.add_process(RobotMove, "move", config_params={"moving_step": 100})

        # Input > Move  > Output
        protocol.add_resource("source", input_robot_model.id, move << "robot")
        protocol.add_output("output", move >> "robot")
        scenario.run()

        lab_credentials = TestHelper.create_lab_credentials()

        # Create a LabModel with credentials linked
        lab = LabModel.get_or_create_current_lab()
        lab.credentials = lab_credentials
        lab.save()

        scenario_count = Scenario.select().count()

        scenario = ScenarioTransfertService.export_scenario_to_lab(
            scenario.get_model().id,
            SendScenarioToLab.build_config(lab.id, "Outputs only", "Force new scenario"),
        )

        self.assertEqual(scenario.status, ScenarioStatus.SUCCESS)
        # there should 4 more scenario, the send, the import scenario, the new copied scenario and
        # the zip resource scenario
        self.assertEqual(Scenario.select().count(), scenario_count + 4)

    def test_archive_round_trip(self):
        """Export a scenario to archive via ScenarioArchiveZipperTask,
        then load it via ScenarioLoaderFromArchive task."""
        setup = ShareScenarioTestSetup(
            self,
            "Archive round trip",
            "archive_tag",
            "archive_value",
            ShareEntityCreateMode.NEW_ID,
        )

        # Export the scenario to a single archive using the zipper task
        scenario_resource = ScenarioResource(setup.initial_scenario_model.id)

        zip_runner = TaskRunner(
            ScenarioArchiveZipperTask,
            params={"resource_mode": "All"},
            inputs={"scenario": scenario_resource},
        )
        zip_outputs = zip_runner.run()

        archive_file: File = zip_outputs["archive"]
        self.assertIsInstance(archive_file, File)
        self.assertTrue(os.path.exists(archive_file.path))
        self.assertTrue(tarfile.is_tarfile(archive_file.path))

        with tarfile.open(archive_file.path, "r") as tar:
            names = tar.getnames()
            self.assertIn(ScenarioArchiveZipper.INFO_JSON_FILE_NAME, names)
            resource_files = [n for n in names if n.startswith("resources/") and n.endswith(".tar")]
            self.assertGreater(len(resource_files), 0)

        # Load the scenario from the archive using the loader task
        load_runner = TaskRunner(
            ScenarioLoaderFromArchive,
            params={"create_option": "Force new scenario"},
            inputs={"archive": archive_file},
        )
        load_outputs = load_runner.run()

        loaded_scenario_resource: ScenarioResource = load_outputs["scenario"]
        self.assertIsInstance(loaded_scenario_resource, ScenarioResource)

        new_scenario = loaded_scenario_resource.get_scenario()
        new_protocol_model = new_scenario.protocol_model
        new_source = cast(TaskModel, new_protocol_model.get_process("source"))
        new_move = cast(TaskModel, new_protocol_model.get_process("move"))
        setup.assert_imported_scenario(new_scenario, new_protocol_model, new_source, new_move)
