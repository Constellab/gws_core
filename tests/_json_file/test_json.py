# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from unittest import TestCase

from gws_core import BaseTestCase, GTest, JSONDict
from gws_core.data_provider.data_provider import DataProvider
from gws_core.impl.file.file import File
from gws_core.impl.json.json_tasks import JSONImporter


# test_json
class TestJson(TestCase):

    def test_json_data(self):
        file_path = DataProvider.get_test_data_path("mini_travel_graph.json")
        json_dict: JSONDict = JSONImporter.call(File(file_path))
        _json = {}
        with open(file_path) as fp:
            _json = json.load(fp)

        # print(d.data)
        self.assertEqual(_json, json_dict.data)
