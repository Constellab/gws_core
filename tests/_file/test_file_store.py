# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import BaseTestCase, File, GTest, LocalFileStore, Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.file_store import FileStore
from gws_core.impl.file.folder import Folder


class TestLocalFileStore(BaseTestCase):

    def test_file(self):
        file_store: FileStore = LocalFileStore()

        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "mini_travel_graph.json")

        # Add a file from a path
        file: File = file_store.add_file_from_path(file_path)
        self.assertTrue(file_store.node_name_exists(file.name))
        self.assertTrue(file.name, 'mini_travel_graph.json')

        # Add a file with the same name
        file_2 = file_store.add_file_from_path(file_path, 'mini_travel_graph.json')
        self.assertTrue(file_store.node_exists(file_2))
        self.assertNotEqual(file_2.path, file.path)

    def test_empty_file(self):
        file_store: FileStore = LocalFileStore()

        # Create an empty file
        empty_file: File = file_store.create_empty_file('test_file.txt')
        self.assertTrue(file_store.node_exists(empty_file))
        self.assertTrue(FileHelper.exists_on_os(empty_file.path))

    def test_empty_folder(self):
        file_store: FileStore = LocalFileStore()

        # Create an empty folder
        folder: Folder = file_store.create_empty_folder('my-folder')
        self.assertTrue(file_store.node_exists(folder))
        self.assertTrue(FileHelper.exists_on_os(folder.path))