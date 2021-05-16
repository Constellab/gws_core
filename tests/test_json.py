# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import json
import unittest

from gws.settings import Settings
from gws.json import JSONData

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")

class TestJson(unittest.TestCase):
    
    def test_json_data(self):
        
        file = os.path.join(testdata_dir, "mini_travel_graph.json")
        d = JSONData._import(file)
        
        _json = {}
        with open(file) as f:
            _json = json.load(f)
        
        print(d.data)
        self.assertEqual(_json, d.kv_data)