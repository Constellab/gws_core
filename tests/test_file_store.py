# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, File, GTest, LocalFileStore,
                      Settings)
from gws_core.impl.file.file_store import FileStore


class TestLocalFileStore(BaseTestCase):

    file_store_instance: FileStore = None

    def test_file_store(self):
        GTest.print("FileStore")
        file_store: FileStore = LocalFileStore()
        TestLocalFileStore.file_store_instance = file_store
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "mini_travel_graph.json")

        file: File = file_store.add_from_path(file_path)
        self.assertTrue(file_store.file_exists(file.name))

        file = file_store.add_from_path(file_path)
        self.assertTrue(file_store.file_exists(file.name))
        self.assertTrue(file_store.contains(file))

        file2 = File()
        file2.path = file_path
        print(file2.path)

        self.assertFalse(file_store.contains(file2))
        file2 = file_store.add_from_file(file2, 'mini_travel_graph.json')
        self.assertTrue(file_store.contains(file2))
        print(file2.path)

        # Add a file with the same name
        file_3 = file_store.add_from_path(file_path, 'mini_travel_graph.json')
        self.assertTrue(file_store.contains(file_3))
