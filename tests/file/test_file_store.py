# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import BaseTestCase, File, GTest, LocalFileStore, Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.file_store import FileStore


class TestLocalFileStore(BaseTestCase):

    def test_file_store(self):
        GTest.print("FileStore")
        file_store: FileStore = LocalFileStore()

        # Create an empty file
        empty_file: File = file_store.create_empty('test_file.txt')
        self.assertTrue(file_store.file_exists(empty_file))
        self.assertTrue(FileHelper.exists_on_os(empty_file.path))

        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "mini_travel_graph.json")

        # Add a file from a path
        file: File = file_store.add_from_path(file_path)
        self.assertTrue(file_store.file_name_exists(file.name))
        self.assertTrue(file.name, 'mini_travel_graph.json')

        # Add a file with the same name
        file_2 = file_store.add_from_path(file_path, 'mini_travel_graph.json')
        self.assertTrue(file_store.file_exists(file_2))
        self.assertNotEqual(file_2.path, file.path)
