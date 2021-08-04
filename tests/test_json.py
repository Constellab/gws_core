# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import unittest

from gws_core import GTest, JSONDict, Settings

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")


class TestJson(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_json_data(self):
        GTest.print("JSONData")
        file = os.path.join(testdata_dir, "mini_travel_graph.json")
        d = JSONDict._import(file)
        _json = {}
        with open(file) as f:
            _json = json.load(f)

        # print(d.data)
        self.assertEqual(_json, d.kv_data)
