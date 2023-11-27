# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from tempfile import SpooledTemporaryFile
from typing import List

from fastapi import UploadFile

from gws_core import (BaseTestCase, File, Folder, FsNodeService,
                      ResourceTyping, resource_decorator)
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.resource.resource_typing import FileTyping


@resource_decorator("SubFile2")
class SubFile(File):

    pass


# test_file_service
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

    def test_get_folder_types(self):
        file_types: List[ResourceTyping] = FsNodeService.get_folder_types()

        # Check that there is at least 1 folder type, Folder
        self.assertTrue(len(file_types) >= 1)

        # Check that the File and SubFile type exists
        self.assertIsNotNone(next(filter(lambda file: Folder == file.get_type(), file_types), None))

    def test_upload_download_file(self):

        upload_file: UploadFile = None

        try:
            upload_file = self._create_upload_file("test.txt", "test")

            # upload the file
            file_model = FsNodeService.upload_file(upload_file, File._typing_name)

            self.assertEqual(file_model.resource_typing_name, File._typing_name)

            # Download the file
            file_response = FsNodeService.download_file(fs_node_id=file_model.id)

            # Check that the file is the same
            self.assertEqual(file_response.filename, 'test.txt')

            # read path
            with open(file_response.path, "r", encoding='utf-8') as f:
                self.assertEqual(f.read(), "test")
        finally:
            if upload_file:
                upload_file.file.close()

    def test_upload_download_folder(self):

        uploaded_files: List[UploadFile] = []

        try:
            uploaded_files.append(self._create_upload_file("hello/test.txt", "test"))
            uploaded_files.append(self._create_upload_file("hello/subHello/test2.txt", "test2"))

            # Upload the folder
            folder_model = FsNodeService.upload_folder(Folder._typing_name, uploaded_files)

            folder_model_path = folder_model.fs_node_model.path
            self.assertEqual(folder_model.resource_typing_name, Folder._typing_name)
            self.assertTrue(FileHelper.is_dir(folder_model_path))
            self.assertTrue(FileHelper.is_file(os.path.join(folder_model_path, "test.txt")))
            self.assertTrue(FileHelper.is_dir(os.path.join(folder_model_path, "subHello")))
            self.assertTrue(FileHelper.is_file(os.path.join(folder_model_path, "subHello", 'test2.txt')))

            # read file 1
            with open(os.path.join(folder_model_path, 'test.txt'), "r", encoding='utf-8') as file:
                self.assertEqual(file.read(), "test")

            # read file 2
            with open(os.path.join(folder_model_path, 'subHello', 'test2.txt'), "r", encoding='utf-8') as file:
                self.assertEqual(file.read(), "test2")

            # Download the folder
            file_response = FsNodeService.download_file(fs_node_id=folder_model.id)
            # Check that the file is the same
            self.assertEqual(file_response.filename, 'hello.zip')

            # Download a file in the folder
            file_response = FsNodeService.download_fsnode_from_folder(folder_model.id, 'test.txt')
            # Check that the file is the same
            self.assertEqual(file_response.filename, 'test.txt')

            # Downlaod a sub folder in the folder
            file_response = FsNodeService.download_fsnode_from_folder(folder_model.id, 'subHello')
            # Check that the file is the same
            self.assertEqual(file_response.filename, 'subHello.zip')
        finally:
            for uploaded_file in uploaded_files:
                uploaded_file.file.close()

    def _create_upload_file(self, file_name: str, content: str) -> UploadFile:

        # Create a file
        folder_path = Settings.make_temp_dir()
        file_path = FileHelper.create_empty_file_if_not_exist(os.path.join(folder_path, "test.txt"))

        # write in the file
        with open(file_path, "w", encoding='utf-8') as file:
            file.write(content)

        spooled_file = SpooledTemporaryFile()

        # Open the source file for reading
        with open(file_path, 'rb') as source_file:
            # Read and write the contents of the source file to the SpooledTemporaryFile
            spooled_file.write(source_file.read())

        # You can now work with spooled_file, which contains the content of the original file
        spooled_file.seek(0)  # Reset the file pointer to the beginning
        return UploadFile(file=spooled_file, filename=file_name)
