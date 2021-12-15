# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os

from gws_core import (BaseTestCase, ConfigParams, File, GTest, JSONDict,
                      Settings)
from gws_core.impl.json.json_tasks import JSONImporter
from gws_core.task.converter.importer_runner import ImporterRunner

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestJson(BaseTestCase):

    async def test_json_data(self):
        GTest.print("JSONDict")
        file_path = os.path.join(testdata_dir, "mini_travel_graph.json")
        json_dict: JSONDict = await ImporterRunner(JSONImporter, file_path).run()
        _json = {}
        with open(file_path) as fp:
            _json = json.load(fp)

        # print(d.data)
        self.assertEqual(_json, json_dict.data)
