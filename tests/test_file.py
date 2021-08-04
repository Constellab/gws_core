# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import unittest

from gws_core import File, GTest, LocalFileStore, Settings


class TestFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_file(self):
        GTest.print("File")

        fs = LocalFileStore()
        f = fs.create_file(name="my_file.txt")
        f.save()
        self.assertTrue(f.is_saved())

        f.write("Hi.\n")
        f.write("My name is John")

        text = f.read()
        self.assertTrue(text, "Hi.\nMy name is John")
        self.assertTrue(f.verify_hash())
