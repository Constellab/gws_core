# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os

from gws_core import GTest, JSONDict, Settings

from tests.base_test import BaseTest

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestJson(BaseTest):

    def test_json_data(self):
        GTest.print("JSONData")
        file = os.path.join(testdata_dir, "mini_travel_graph.json")
        json_dict: JSONDict = JSONDict.import_resource(file)
        _json = {}
        with open(file) as file:
            _json = json.load(file)

        # print(d.data)
        self.assertEqual(_json, json_dict.data)
