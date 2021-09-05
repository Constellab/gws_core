# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, FileResource, FileResourceModel, FileService, GTest,
                      LocalFileStore)


class TestFile(BaseTestCase):

    def test_file(self):
        GTest.print("File")

        file_store: LocalFileStore = LocalFileStore()
        file_resource_1: FileResource = file_store.create_file("my_file.txt")
        file_resource_model: FileResourceModel = FileService.create_file_resource(file=file_resource_1)
        
        self.assertTrue(file_resource_model.is_saved())
        self.assertEqual(file_resource_model.path, file_resource_1.path)

        file_resource_2: FileResource = file_resource_model.get_resource()
        file_resource_3: FileResource = file_resource_model.get_resource()
        self.assertNotEqual(file_resource_1, file_resource_2)
        self.assertEqual(file_resource_2, file_resource_3) # use cached data

        self.assertEqual(file_resource_1.path, file_resource_2.path)
        self.assertEqual(file_resource_2.path, file_resource_3.path)
        self.assertEqual(file_resource_model.path, file_resource_2.path)
        file_resource_2.write("Hi.\n")
        file_resource_2.write("My name is John")

        text = file_resource_1.read()
        self.assertEqual(text, "Hi.\nMy name is John")
        self.assertTrue(file_resource_model.verify_hash())
