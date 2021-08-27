# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import File, FileResource, FileService, GTest, LocalFileStore

from tests.base_test import BaseTest


class TestFile(BaseTest):

    def test_file(self):
        GTest.print("File")

        file_store: LocalFileStore = LocalFileStore()
        file: File = file_store.create_file(name="my_file.txt")
        file_resource: FileResource = FileService.create_file_resource(file=file)
        self.assertTrue(file_resource.is_saved())

        file: File = file_resource.get_resource()
        file.write("Hi.\n")
        file.write("My name is John")

        text = file.read()
        self.assertTrue(text, "Hi.\nMy name is John")
        self.assertTrue(file_resource.verify_hash())
