import os
from datetime import datetime, timedelta

from pandas import DataFrame

from gws_core import (
    BaseTestCase,
    ConfigParams,
    File,
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
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.resource.resource_transfert_service import ResourceTransfertService
from gws_core.resource.task.resource_downloader_http import ResourceDownloaderHttp
from gws_core.resource.task.send_resource_to_lab import SendResourceToLab
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.share.share_link import ShareLink
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.share_service import ShareService
from gws_core.share.shared_dto import (
    GenerateShareLinkDTO,
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


def get_table() -> Table:
    df = DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    return Table(df)


def get_file() -> File:
    dir = Settings.get_instance().make_temp_dir()
    file_path = os.path.join(dir, "test.txt")
    with open(file_path, "w", encoding="UTF-8") as f:
        f.write("test")
    return File(file_path)


@task_decorator(unique_name="GenerateResourceSet")
class GenerateResourceSet(Task):
    output_specs = OutputSpecs({"resource_set": OutputSpec(ResourceSet)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # create a simple resource
        table = get_table()

        # save the resource model
        file = get_file()

        resource_set: ResourceSet = ResourceSet()
        resource_set.add_resource(table, "table")
        resource_set.add_resource(file, "file")

        return {"resource_set": resource_set}


@task_decorator(unique_name="GenerateResourceList")
class GenerateResourceList(Task):
    output_specs = OutputSpecs({"resource_list": OutputSpec(ResourceList)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # create a simple resource
        table = get_table()

        # save the resource model
        file = get_file()

        resource_list: ResourceList = ResourceList()
        resource_list.add_resource(table)
        resource_list.add_resource(file)

        return {"resource_list": resource_list}


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

    def test_share_file_resource(self):
        # save the resource model
        file = get_file()

        original_resource_model = ResourceModel.save_from_resource(
            file, origin=ResourceOrigin.UPLOADED
        )

        new_resource_model = self._generate_link_and_download_resource(original_resource_model.id)
        resource: File = new_resource_model.get_resource()

        self.assertEqual(resource.name, "test.txt")
        # check that the path is different form the original
        self.assertNotEqual(resource.path, original_resource_model.fs_node_model.path)
        self.assertEqual("test", resource.read())

    def test_share_resource_set(self):
        # Generate a resource set
        i_scenario: ScenarioProxy = ScenarioProxy()
        i_scenario.get_protocol().add_process(GenerateResourceSet, "generate_resource_set")
        i_scenario.run()
        i_process = i_scenario.get_protocol().get_process("generate_resource_set")
        resource_model_id = i_process.get_output_resource_model("resource_set").id

        original_resource_model = ResourceService.get_by_id_and_check(resource_model_id)
        original_resource_set: ResourceSet = original_resource_model.get_resource()

        new_resource_model = self._generate_link_and_download_resource(original_resource_model.id)

        resource_set: ResourceSet = new_resource_model.get_resource()
        self.assertIsInstance(resource_set, ResourceSet)
        self.assertEqual(2, len(resource_set))

        # check the table
        table: Table = resource_set.get_resource("table")
        self.assertIsNotNone(table)
        original_table: Table = original_resource_set.get_resource("table")
        # check that this is a new resource
        self.assertNotEqual(original_table.get_model_id(), table.get_model_id())
        self.assertTrue(original_table.equals(table))

        # check the file
        file: File = resource_set.get_resource("file")
        self.assertIsNotNone(file)
        self.assertEqual("test", file.read())
        original_file = original_resource_set.get_resource("file")
        # check that this is a new resource
        self.assertNotEqual(original_file.get_model_id(), file.get_model_id())

    def test_share_resource_list(self):
        # Generate a resource list
        i_scenario: ScenarioProxy = ScenarioProxy()
        i_scenario.get_protocol().add_process(GenerateResourceList, "generate_resource_list")
        i_scenario.run()
        i_process = i_scenario.get_protocol().get_process("generate_resource_list")
        resource_model_id = i_process.get_output_resource_model("resource_list").id

        original_resource_model = ResourceService.get_by_id_and_check(resource_model_id)
        original_resource_list: ResourceList = original_resource_model.get_resource()

        new_resource_model = self._generate_link_and_download_resource(original_resource_model.id)
        resource_list: ResourceList = new_resource_model.get_resource()

        self.assertIsInstance(resource_list, ResourceList)
        self.assertEqual(2, len(resource_list))

        # check the table
        table: Table = resource_list[0]
        self.assertIsNotNone(table)
        original_table: Table = original_resource_list[0]
        # check that this is a new resource
        self.assertNotEqual(original_table.get_model_id(), table.get_model_id())
        self.assertTrue(original_table.equals(table))

        # check the file
        file: File = resource_list[1]
        self.assertIsNotNone(file)
        self.assertEqual("test", file.read())
        original_file = original_resource_list[1]
        # check that this is a new resource
        self.assertNotEqual(original_file.get_model_id(), file.get_model_id())

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
