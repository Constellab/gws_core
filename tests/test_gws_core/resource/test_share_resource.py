import os
from datetime import datetime, timedelta
from typing import cast
from unittest import TestCase

from gws_core import (
    BaseTestCase,
    ConfigParams,
    File,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    ResourceModel,
    ResourceSet,
    ScenarioProxy,
    Settings,
    Table,
    Task,
    TaskInputs,
    TaskOutputs,
    task_decorator,
)
from gws_core.entity_navigator.entity_navigator_service import EntityNavigatorService
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.resource.resource_builder import ResourceZipBuilder
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_loader import ResourceLoader
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.resource.resource_transfert_service import ResourceTransfertService
from gws_core.resource.resource_zipper import ResourceZipper
from gws_core.resource.task.resource_downloader_http import ResourceDownloaderHttp
from gws_core.resource.task.send_resource_to_lab import SendResourceToLab
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.share.share_link import ShareLink
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.share_service import ShareService
from gws_core.share.shared_dto import (
    GenerateShareLinkDTO,
    ShareEntityCreateMode,
    ShareLinkEntityType,
    ShareLinkType,
    ShareResourceInfoReponseDTO,
)
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigins
from gws_core.tag.tag_dto import TagOriginType
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.test.test_helper import TestHelper
from gws_core.test.test_start_unvicorn_app import TestStartUvicornApp
from gws_core.user.current_user_service import CurrentUserService
from pandas import DataFrame


def get_table() -> Table:
    df = DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    table = Table(df)
    table.name = "MyTestName"
    table.set_all_column_tags([{"name": "tag1"}, {"name": "tag2"}])
    table.tags.add_tag(
        Tag("resource_tag", "resource_tag_value", origins=TagOrigins(TagOriginType.USER, "test"))
    )
    return table


def get_file() -> File:
    dir = Settings.get_instance().make_temp_dir()
    file_path = os.path.join(dir, "test.txt")
    with open(file_path, "w", encoding="UTF-8") as f:
        f.write("test")
    return File(file_path)


@task_decorator(unique_name="GenerateResourceSet")
class GenerateResourceSet(Task):
    input_specs = InputSpecs({"robot": InputSpec(Robot)})
    output_specs = OutputSpecs({"resource_set": OutputSpec(ResourceSet)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # Get the input robot
        robot = inputs.get("robot")

        # create a simple resource
        table = get_table()

        # save the resource model
        file = get_file()

        resource_set: ResourceSet = ResourceSet()
        # Add the input robot that was already created and saved
        resource_set.add_resource(robot, "robot", create_new_resource=False)
        resource_set.add_resource(table, "table")
        resource_set.add_resource(file, "file")

        return {"resource_set": resource_set}


@task_decorator(unique_name="GenerateResourceList")
class GenerateResourceList(Task):
    input_specs = InputSpecs({"robot": InputSpec(Robot)})
    output_specs = OutputSpecs({"resource_list": OutputSpec(ResourceList)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # Get the input robot
        robot = inputs.get("robot")

        # create a simple resource
        table = get_table()

        # save the resource model
        file = get_file()

        resource_list: ResourceList = ResourceList()
        # Add the input robot that was already created and saved
        resource_list.add_resource(robot, create_new_resource=False)
        resource_list.add_resource(table)
        resource_list.add_resource(file)

        return {"resource_list": resource_list}


class ShareResourceTestSetup:
    """Helper class that creates a resource, zips it, and provides assertion methods.

    Supports both NEW_ID and KEEP_ID create modes for testing resource sharing.

    Attributes
    ----------
    original_resource_model : ResourceModel
        The original resource model before sharing.
    create_mode : ShareEntityCreateMode
        The create mode used for this test setup.
    """

    original_resource_model: ResourceModel
    _children_resource_models: dict[str, ResourceModel]
    _original_resource_set: ResourceSet
    _original_resource_list: ResourceList

    create_mode: ShareEntityCreateMode
    _tc: TestCase

    def __init__(self, test_case: TestCase, create_mode: ShareEntityCreateMode) -> None:
        self._tc = test_case
        self.create_mode = create_mode

    def _check_id(self, imported_id: str, original_id: str) -> None:
        """Assert that imported_id equals or differs from original_id depending on create_mode."""
        if self.create_mode == ShareEntityCreateMode.KEEP_ID:
            self._tc.assertEqual(imported_id, original_id)
        else:
            self._tc.assertNotEqual(imported_id, original_id)

    def _zip_resource(self, resource_model_id: str) -> str:
        """Zip a resource and return the zip file path."""
        current_user = CurrentUserService.get_and_check_current_user()
        zipper = ResourceZipper(current_user)
        zipper.add_resource_model(resource_model_id)
        zipper.close_zip()
        return zipper.get_zip_file_path()

    def build_resource_from_zip(self, zip_path: str) -> ResourceModel:
        """Use ResourceZipBuilder to import a resource from a zip file with the configured create_mode."""
        current_user = CurrentUserService.get_and_check_current_user()
        origin = ExternalLabApiService.get_current_lab_info(current_user)

        resource_loader = ResourceLoader.from_compress_file(
            zip_path, skip_tags=False, mode=self.create_mode
        )
        builder = ResourceZipBuilder(
            resource_loader=resource_loader,
            origin=origin,
            create_mode=self.create_mode,
        )
        try:
            return builder.save()
        finally:
            builder.cleanup()

    def _delete_resource(self, resource_model_id: str) -> None:
        """Delete a resource model and its children from the DB."""
        # Delete children first to avoid FK constraint violations
        EntityNavigatorService.delete_resource(resource_model_id)

    def setup_and_import_basic_resource(self) -> ResourceModel:
        """Create a table resource, zip it, optionally delete original, and import via ResourceBuilder."""
        table = get_table()
        table.name = "MyTestName"
        table.set_all_column_tags([{"name": "tag1"}, {"name": "tag2"}])
        table.tags.add_tag(
            Tag(
                "resource_tag", "resource_tag_value", origins=TagOrigins(TagOriginType.USER, "test")
            )
        )

        self.original_resource_model = ResourceModel.save_from_resource(
            table, origin=ResourceOrigin.UPLOADED
        )

        zip_path = self._zip_resource(self.original_resource_model.id)

        self._delete_resource(self.original_resource_model.id)

        return self.build_resource_from_zip(zip_path)

    def _assert_new_resource_model(
        self, new_resource_model: ResourceModel, original_resource_model: ResourceModel
    ) -> None:
        self._check_id(new_resource_model.id, original_resource_model.id)
        self._tc.assertEqual(new_resource_model.origin, ResourceOrigin.IMPORTED_FROM_LAB)
        # the scenario and task should not be set on the resource model of the imported resource because
        # they should not exist
        self._tc.assertEqual(new_resource_model.name, original_resource_model.name)
        self._tc.assertEqual(
            new_resource_model.resource_typing_name, original_resource_model.resource_typing_name
        )
        self._tc.assertIsNone(new_resource_model.scenario)
        self._tc.assertIsNone(new_resource_model.task_model)

    def _assert_new_child_resource_model(
        self,
        child_resource_model: ResourceModel,
        original_child_resource_model: ResourceModel,
        new_parent_resource_model_id: str | None,
    ) -> None:
        self._assert_new_resource_model(child_resource_model, original_child_resource_model)
        self._tc.assertEqual(child_resource_model.parent_resource_id, new_parent_resource_model_id)

    def assert_imported_basic_resource(self, new_resource_model: ResourceModel) -> None:
        """Assert that a basic table resource was imported correctly."""
        self._assert_new_resource_model(new_resource_model, self.original_resource_model)

        new_table = cast(Table, new_resource_model.get_resource())

        # Check the tags
        tags = EntityTagList.find_by_entity(TagEntityType.RESOURCE, new_resource_model.id)
        self._tc.assertEqual(len(tags.get_tags()), 1)
        self._tc.assertTrue(new_table.tags.has_tag(Tag("resource_tag", "resource_tag_value")))
        tag = new_table.tags.get_tag("resource_tag", "resource_tag_value")
        self._tc.assertTrue(tag.origins.has_origin(TagOriginType.USER, "test"))
        self._tc.assertIsNotNone(tag.origins.get_origins()[0].external_lab_origin_id)

        self._tc.assertIsInstance(new_table, Table)
        self._tc.assertEqual(new_table.name, "MyTestName")
        self._tc.assertTrue(new_table.equals(get_table()))

        # Check the tags

        # test that the origin of the resource exist
        shared_resource = ResourceService.get_shared_resource_origin_info(new_resource_model.id)
        self._tc.assertEqual(shared_resource.entity.id, new_resource_model.id)

    def setup_and_import_file_resource(self) -> ResourceModel:
        """Create a file resource, zip it, optionally delete original, and import via ResourceBuilder."""
        file = get_file()

        self.original_resource_model = ResourceModel.save_from_resource(
            file, origin=ResourceOrigin.UPLOADED
        )

        zip_path = self._zip_resource(self.original_resource_model.id)

        self._delete_resource(self.original_resource_model.id)

        return self.build_resource_from_zip(zip_path)

    def assert_imported_file_resource(self, new_resource_model: ResourceModel) -> None:
        """Assert that a file resource was imported correctly."""
        self._assert_new_resource_model(new_resource_model, self.original_resource_model)
        self._tc.assertIsNotNone(new_resource_model.fs_node_model)

        resource: File = new_resource_model.get_resource()
        self._tc.assertTrue(resource.name.startswith("test"))
        self._tc.assertEqual("test", resource.read())

    def setup_and_import_resource_set(self) -> ResourceModel:
        """Create a resource set via scenario, zip it, optionally delete original,
        and import via ResourceBuilder."""
        i_scenario: ScenarioProxy = ScenarioProxy()
        robot_create = i_scenario.get_protocol().add_process(RobotCreate, "robot_create")
        generate_resource_set = i_scenario.get_protocol().add_process(
            GenerateResourceSet, "generate_resource_set"
        )
        i_scenario.get_protocol().add_connectors(
            [(robot_create >> "robot", generate_resource_set << "robot")]
        )
        i_scenario.run()
        i_process = i_scenario.get_protocol().get_process("generate_resource_set")
        resource_model_id = i_process.get_output_resource_model("resource_set").id

        self.original_resource_model = ResourceService.get_by_id_and_check(resource_model_id)
        self._original_resource_set: ResourceSet = self.original_resource_model.get_resource()

        zip_path = self._zip_resource(self.original_resource_model.id)

        # store the children resource models
        self._children_resource_models = {
            "robot": ResourceModel.get_by_id_and_check(
                self._original_resource_set.get_resource("robot").get_model_id()
            ),
            "table": ResourceModel.get_by_id_and_check(
                self._original_resource_set.get_resource("table").get_model_id()
            ),
            "file": ResourceModel.get_by_id_and_check(
                self._original_resource_set.get_resource("file").get_model_id()
            ),
        }

        i_scenario.delete()

        return self.build_resource_from_zip(zip_path)

    def assert_imported_resource_set(self, new_resource_model: ResourceModel) -> None:
        """Assert that a resource set was imported correctly."""
        self._assert_new_resource_model(new_resource_model, self.original_resource_model)

        resource_set: ResourceSet = new_resource_model.get_resource()
        self._tc.assertIsInstance(resource_set, ResourceSet)
        self._tc.assertEqual(3, len(resource_set))

        # check the robot
        robot: Robot = resource_set.get_resource("robot")
        self._tc.assertIsNotNone(robot)
        robot_model = ResourceModel.get_by_id_and_check(robot.get_model_id())
        # The robot should not have the parent resource model id
        self._assert_new_child_resource_model(
            robot_model, self._children_resource_models["robot"], None
        )

        original_robot: Robot = self._original_resource_set.get_resource("robot")
        self._check_id(robot.get_model_id(), original_robot.get_model_id())
        self._tc.assertEqual(original_robot.age, robot.age)

        # check the table
        table: Table = resource_set.get_resource("table")
        self._tc.assertIsNotNone(table)
        table_model = ResourceModel.get_by_id_and_check(table.get_model_id())
        self._assert_new_child_resource_model(
            table_model, self._children_resource_models["table"], new_resource_model.id
        )
        self._tc.assertTrue(table.equals(get_table()))

        # check the file
        file: File = resource_set.get_resource("file")
        self._tc.assertIsNotNone(file)
        file_model = ResourceModel.get_by_id_and_check(file.get_model_id())
        self._assert_new_child_resource_model(
            file_model, self._children_resource_models["file"], new_resource_model.id
        )
        self._tc.assertEqual("test", file.read())

    def setup_and_import_resource_list(self) -> ResourceModel:
        """Create a resource list via scenario, zip it, optionally delete original,
        and import via ResourceBuilder."""
        i_scenario: ScenarioProxy = ScenarioProxy()
        robot_create = i_scenario.get_protocol().add_process(RobotCreate, "robot_create")
        generate_resource_list = i_scenario.get_protocol().add_process(
            GenerateResourceList, "generate_resource_list"
        )
        i_scenario.get_protocol().add_connectors(
            [(robot_create >> "robot", generate_resource_list << "robot")]
        )
        i_scenario.run()
        i_process = i_scenario.get_protocol().get_process("generate_resource_list")
        resource_model_id = i_process.get_output_resource_model("resource_list").id

        self.original_resource_model = ResourceService.get_by_id_and_check(resource_model_id)
        self._original_resource_list: ResourceList = self.original_resource_model.get_resource()

        self._children_resource_models = {
            "robot": ResourceModel.get_by_id_and_check(
                self._original_resource_list[0].get_model_id()
            ),
            "table": ResourceModel.get_by_id_and_check(
                self._original_resource_list[1].get_model_id()
            ),
            "file": ResourceModel.get_by_id_and_check(
                self._original_resource_list[2].get_model_id()
            ),
        }

        zip_path = self._zip_resource(self.original_resource_model.id)
        i_scenario.delete()

        return self.build_resource_from_zip(zip_path)

    def assert_imported_resource_list(self, new_resource_model: ResourceModel) -> None:
        """Assert that a resource list was imported correctly."""
        self._assert_new_resource_model(new_resource_model, self.original_resource_model)

        resource_list: ResourceList = new_resource_model.get_resource()
        self._tc.assertIsInstance(resource_list, ResourceList)
        self._tc.assertEqual(3, len(resource_list))

        # check the robot
        robot: Robot = resource_list[0]
        self._tc.assertIsNotNone(robot)
        robot_model = ResourceModel.get_by_id_and_check(robot.get_model_id())
        # The robot should not have the parent resource model id
        self._assert_new_child_resource_model(
            robot_model, self._children_resource_models["robot"], None
        )
        original_robot: Robot = self._original_resource_list[0]
        self._check_id(robot.get_model_id(), original_robot.get_model_id())
        self._tc.assertEqual(original_robot.age, robot.age)

        # check the table
        table: Table = resource_list[1]
        self._tc.assertIsNotNone(table)
        table_model = ResourceModel.get_by_id_and_check(table.get_model_id())
        self._assert_new_child_resource_model(
            table_model, self._children_resource_models["table"], new_resource_model.id
        )
        self._tc.assertTrue(table.equals(get_table()))

        # check the file
        file: File = resource_list[2]
        self._tc.assertIsNotNone(file)
        file_model = ResourceModel.get_by_id_and_check(file.get_model_id())
        self._assert_new_child_resource_model(
            file_model, self._children_resource_models["file"], new_resource_model.id
        )
        self._tc.assertEqual("test", file.read())


# test_share_resource
class TestShareResource(BaseTestCase):
    start_uvicorn_app: TestStartUvicornApp

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

    def test_share_basic_resource(self):
        # create a simple resource
        table = get_table()
        table.name = "MyTestName"
        table.set_all_column_tags([{"name": "tag1"}, {"name": "tag2"}])
        table.tags.add_tag(
            Tag(
                "resource_tag", "resource_tag_value", origins=TagOrigins(TagOriginType.USER, "test")
            )
        )

        # save the resource model
        original_resource_model = ResourceModel.save_from_resource(
            table, origin=ResourceOrigin.UPLOADED
        )

        new_resource_model = self._generate_link_and_download_resource(original_resource_model.id)
        share_link = (
            ShareLink.select().where(ShareLink.entity_id == original_resource_model.id).first()
        )

        # get the share entity info
        share_entity_info: ShareResourceInfoReponseDTO = (
            ShareService.get_resource_entity_object_info(share_link)
        )
        self.assertEqual(share_entity_info.entity_type, ShareLinkEntityType.RESOURCE)
        self.assertEqual(share_entity_info.entity_id, original_resource_model.id)
        self.assertIsNotNone(share_entity_info.zip_entity_route)
        # check that there is only one resource
        self.assertTrue(len(share_entity_info.entity_object), 1)

        new_table: Table = new_resource_model.get_resource()

        # Check the tags
        tags = EntityTagList.find_by_entity(TagEntityType.RESOURCE, new_resource_model.id)
        self.assertEqual(len(tags.get_tags()), 1)
        tag = tags.get_tags()[0]

        self.assertIsInstance(new_table, Table)
        self.assertTrue(table.equals(new_table))
        self.assertEqual(new_table.name, "MyTestName")
        self.assertTrue(new_table.tags.has_tag(Tag("resource_tag", "resource_tag_value")))
        tag = new_table.tags.get_tag("resource_tag", "resource_tag_value")
        self.assertTrue(tag.origins.has_origin(TagOriginType.USER, "test"))
        self.assertIsNotNone(tag.origins.get_origins()[0].external_lab_origin_id)

        # test that the origin of the resource exist
        shared_resource = ResourceService.get_shared_resource_origin_info(new_resource_model.id)
        self.assertEqual(shared_resource.entity.id, new_resource_model.id)

    def test_share_basic_resource_with_builder(self):
        """Test basic resource sharing using ResourceBuilder in both NEW_ID and KEEP_ID modes."""
        # Test NEW_ID mode
        setup_new = ShareResourceTestSetup(self, ShareEntityCreateMode.NEW_ID)
        new_resource_model = setup_new.setup_and_import_basic_resource()
        setup_new.assert_imported_basic_resource(new_resource_model)

        # Test KEEP_ID mode
        setup_keep = ShareResourceTestSetup(self, ShareEntityCreateMode.KEEP_ID)
        new_resource_model = setup_keep.setup_and_import_basic_resource()
        setup_keep.assert_imported_basic_resource(new_resource_model)

    def test_share_file_resource_with_builder(self):
        """Test file resource sharing using ResourceBuilder in both NEW_ID and KEEP_ID modes."""
        # Test NEW_ID mode
        setup_new = ShareResourceTestSetup(self, ShareEntityCreateMode.NEW_ID)
        new_resource_model = setup_new.setup_and_import_file_resource()
        setup_new.assert_imported_file_resource(new_resource_model)

        # Test KEEP_ID mode
        setup_keep = ShareResourceTestSetup(self, ShareEntityCreateMode.KEEP_ID)
        new_resource_model = setup_keep.setup_and_import_file_resource()
        setup_keep.assert_imported_file_resource(new_resource_model)

    def test_share_resource_set_with_builder(self):
        """Test resource set sharing using ResourceBuilder in both NEW_ID and KEEP_ID modes."""
        # Test NEW_ID mode
        setup_new = ShareResourceTestSetup(self, ShareEntityCreateMode.NEW_ID)
        new_resource_model = setup_new.setup_and_import_resource_set()
        setup_new.assert_imported_resource_set(new_resource_model)

        # Test KEEP_ID mode
        setup_keep = ShareResourceTestSetup(self, ShareEntityCreateMode.KEEP_ID)
        new_resource_model = setup_keep.setup_and_import_resource_set()
        setup_keep.assert_imported_resource_set(new_resource_model)

    def test_share_resource_list_with_builder(self):
        """Test resource list sharing using ResourceBuilder in both NEW_ID and KEEP_ID modes."""
        # Test NEW_ID mode
        setup_new = ShareResourceTestSetup(self, ShareEntityCreateMode.NEW_ID)
        new_resource_model = setup_new.setup_and_import_resource_list()
        setup_new.assert_imported_resource_list(new_resource_model)

        # Test KEEP_ID mode
        setup_keep = ShareResourceTestSetup(self, ShareEntityCreateMode.KEEP_ID)
        new_resource_model = setup_keep.setup_and_import_resource_list()
        setup_keep.assert_imported_resource_list(new_resource_model)

    def _generate_link_and_download_resource(self, original_resource_id) -> ResourceModel:
        # create a share link
        generate_dto = GenerateShareLinkDTO(
            entity_id=original_resource_id,
            entity_type=ShareLinkEntityType.RESOURCE,
            valid_until=datetime.now() + timedelta(days=1),
        )
        share_link = ShareLinkService.generate_share_link(generate_dto, ShareLinkType.PUBLIC)

        return ResourceTransfertService.import_resource_from_link_sync(
            ResourceDownloaderHttp.build_config(
                share_link.get_download_link(), "auto", "Force new resource"
            )
        )

    def test_send_resource_to_lab(self):
        # create a simple resource
        table = get_table()

        # save the resource model
        original_resource_model = ResourceModel.save_from_resource(
            table, origin=ResourceOrigin.UPLOADED
        )

        lab_credentials = TestHelper.create_lab_credentials()

        # Call the external lab API to import the resource
        scenario = ResourceTransfertService.export_resource_to_lab(
            original_resource_model.id,
            SendResourceToLab.build_config(lab_credentials.name, 1, "Force new resource"),
        )

        self.assertEqual(scenario.status, ScenarioStatus.SUCCESS)
