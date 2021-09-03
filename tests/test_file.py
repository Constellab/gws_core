# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, File, FileResourceModel, FileService, GTest,
                      LocalFileStore)


class TestFile(BaseTestCase):

    def test_file(self):
        GTest.print("File")

        file_store: LocalFileStore = LocalFileStore()
        file: File = file_store.create_file("my_file.txt")
        file_resource_model: FileResourceModel = FileService.create_file_resource(file=file)
        self.assertTrue(file_resource_model.is_saved())

        file: File = file_resource_model.get_resource()
        file.write("Hi.\n")
        file.write("My name is John")

        text = file.read()
        self.assertTrue(text, "Hi.\nMy name is John")
        self.assertTrue(file_resource_model.verify_hash())
