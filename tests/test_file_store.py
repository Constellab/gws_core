# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import unittest

from gws_core import File, GTest, LocalFileStore, Settings


class TestLocalFileStore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_file_store(self):
        GTest.print("FileStore")
        fs = LocalFileStore()
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "mini_travel_graph.json")

        file = fs.add(file_path)
        self.assertTrue(file.exists())

        file = fs.add(file_path)
        self.assertTrue(file.exists())
        self.assertTrue(fs.contains(file))

        file2 = File()
        file2.path = file_path
        print(file2.path)

        self.assertFalse(fs.contains(file2))
        file2.move_to_store(fs)
        self.assertTrue(fs.contains(file2))
        print(file2.path)
