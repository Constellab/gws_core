

from typing import List

from fastapi.testclient import TestClient
from gws_core import (BaseTestCase, File, FsNodeService, ResourceTyping,
                      resource_decorator)
from gws_core.app import app
from gws_core.core_app import core_app
from gws_core.impl.table.table_file import TableFile
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.resource_typing import FileTyping
from tests.gws_core_test_helper import GwsCoreTestHelper

client = TestClient(app)
client2 = TestClient(core_app)


@resource_decorator("SubFile")
class SubFile(File):

    supported_extensions: List[str] = ['super']


class TestFileService(BaseTestCase):

    def test_get_file_types(self):

        file_types: List[ResourceTyping] = FsNodeService.get_file_types()

        # Check that there is at least 2 files type, File and SubFile
        self.assertTrue(len(file_types) >= 2)

        # Check that the File and SubFile type exists
        self.assertIsNotNone(next(filter(lambda file: File == file.get_type(), file_types), None))

        sub_file_type: FileTyping = next(filter(lambda file: SubFile == file.get_type(), file_types), None)
        self.assertIsNotNone(sub_file_type)
        self.assertIsInstance(sub_file_type, FileTyping)

        # Check that to_json contains default extension
        self.assertEqual(sub_file_type.to_json()["supported_extensions"], ['super'])

    def test_upload_and_delete(self):
        file: File = GwsCoreTestHelper.get_iris_file()

        resource_model: ResourceModel = FsNodeService.create_fs_node_model(file)
        ResourceService.delete(resource_model.id)

        self.assertIsNone(ResourceModel.get_by_id(resource_model.id))

    def test_update_type(self):
        file: File = GwsCoreTestHelper.get_iris_file()

        resource_model: ResourceModel = FsNodeService.create_fs_node_model(file)
        self.assertIsInstance(resource_model.get_resource(), File)
        self.assertNotIsInstance(resource_model.get_resource(), TableFile)

        FsNodeService.update_file_type(resource_model.id, TableFile._typing_name)

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_model.id)
        self.assertIsInstance(resource_model.get_resource(), TableFile)
