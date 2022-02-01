

from typing import List

from fastapi.testclient import TestClient
from gws_core import (BaseTestCase, File, Folder, FsNodeService,
                      ResourceTyping, resource_decorator)
from gws_core.app import app
from gws_core.core_app import core_app
from gws_core.resource.resource_typing import FileTyping

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

    def test_get_folder_types(self):
        file_types: List[ResourceTyping] = FsNodeService.get_folder_types()

        # Check that there is at least 1 folder type, Folder
        self.assertTrue(len(file_types) >= 1)

        # Check that the File and SubFile type exists
        self.assertIsNotNone(next(filter(lambda file: Folder == file.get_type(), file_types), None))
