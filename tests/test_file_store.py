# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import File, GTest, LocalFileStore, Settings

from tests.base_test import BaseTest


class TestLocalFileStore(BaseTest):

    def test_file_store(self):
        GTest.print("FileStore")
        file_store = LocalFileStore()
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "mini_travel_graph.json")

        file: File = file_store.add(file_path)
        self.assertTrue(file.exists())

        file = file_store.add(file_path)
        self.assertTrue(file.exists())
        self.assertTrue(file_store.contains(file))

        file2 = File()
        file2.path = file_path
        print(file2.path)

        self.assertFalse(file_store.contains(file2))
        file2.move_to_store(file_store)
        self.assertTrue(file_store.contains(file2))
        print(file2.path)
