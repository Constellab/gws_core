# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json

from gws_core import BaseTestCase, GTest, JSONDict
from gws_core.impl.json.json_tasks import JSONImporter
from tests.gws_core_test_helper import GwsCoreTestHelper


class TestJson(BaseTestCase):

    def test_json_data(self):
        GTest.print("JSONDict")
        file_path = GwsCoreTestHelper.get_test_data_path("mini_travel_graph.json")
        json_dict: JSONDict = JSONImporter.call(file_path)
        _json = {}
        with open(file_path) as fp:
            _json = json.load(fp)

        # print(d.data)
        self.assertEqual(_json, json_dict.data)
