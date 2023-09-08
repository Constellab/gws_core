# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
from unittest import TestCase

from numpy import NaN, inf

from gws_core import JSONDict
from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.json_helper import JSONHelper
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.impl.json.json_tasks import JSONExporter, JSONImporter
from gws_core.test.data_provider import DataProvider


class ATest():

    a_test: str = None

    def __init__(self, a_test: str) -> None:
        self.a_test = a_test

    def __str__(self) -> str:
        return self.a_test


# test_json
class TestJson(TestCase):

    def test_importer(self):
        file_path = DataProvider.get_test_data_path("mini_travel_graph.json")
        json_dict: JSONDict = JSONImporter.call(File(file_path))
        json_ = {}
        with open(file_path, encoding='utf-8') as file_path:
            json_ = json.load(file_path)

        # print(d.data)
        self.assertEqual(json_, json_dict.data)

    def test_exporter(self):
        dict_ = {'hello': 123, 'numpy': NaN, 'inf': inf, 'a': ATest(a_test="hello")}

        json_dict = JSONDict(dict_)
        file_path = os.path.join(Settings.make_temp_dir(), "test_exporter.json")

        file: File = JSONExporter.call(json_dict)

        json_ = {}
        with open(file.path, encoding='utf-8') as file_path:
            json_ = json.load(file_path)

        self.assertEqual(json_, {'hello': 123, 'numpy': None, 'inf': None, 'a': 'hello'})

    def test_dict_to_json(self):
        self.assertEqual(JSONHelper.convert_dict_to_json(
            {'hello': 123, 'numpy': NaN, 'inf': inf, 'a': ATest(a_test="hello")}),
            {'hello': 123, 'numpy': None, 'inf': None, 'a': 'hello'})

        self.assertEqual(JSONHelper.convert_dict_to_json("dict_"), "dict_")
        self.assertEqual(JSONHelper.convert_dict_to_json(12), 12)

        dict_ = JSONDict({'hello': 123, 'numpy': NaN, 'inf': inf, 'a': ATest(a_test="hello")})
        self.assertEqual(dict_.default_view(ConfigParams()).data_to_dict(ConfigParams()), {
                         'hello': 123, 'numpy': None, 'inf': None, 'a': 'hello'})
