import json
import os

from numpy import NaN, inf

from gws_core import JSONDict
from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.json_helper import JSONHelper
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.impl.json.json_tasks import JSONExporter, JSONImporter
from gws_core.test.base_test_case_light import BaseTestCaseLight
from gws_core.test.data_provider import DataProvider


class ATest:
    a_test: str = None

    def __init__(self, a_test: str) -> None:
        self.a_test = a_test

    def __str__(self) -> str:
        return self.a_test


# test_json
class TestJson(BaseTestCaseLight):
    def test_importer(self):
        file_path = DataProvider.get_test_data_path("sample.json")
        json_dict: JSONDict = JSONImporter.call(File(file_path))
        json_ = {}
        with open(file_path, encoding="utf-8") as file_path:
            json_ = json.load(file_path)

        self.assertEqual(json_, json_dict.data)

    def test_exporter(self):
        dict_ = {"hello": 123, "numpy": NaN, "inf": inf, "a": ATest(a_test="hello")}

        json_dict = JSONDict(dict_)
        file_path = os.path.join(Settings.make_temp_dir(), "test_exporter.json")

        file: File = JSONExporter.call(json_dict)

        json_ = {}
        with open(file.path, encoding="utf-8") as file_path:
            json_ = json.load(file_path)

        self.assertEqual(json_, {"hello": 123, "numpy": None, "inf": None, "a": "hello"})

    def test_dict_to_json(self):
        self.assertEqual(
            JSONHelper.convert_dict_to_json(
                {"hello": 123, "numpy": NaN, "inf": inf, "a": ATest(a_test="hello")}
            ),
            {"hello": 123, "numpy": None, "inf": None, "a": "hello"},
        )

        self.assertEqual(JSONHelper.convert_dict_to_json("dict_"), "dict_")
        self.assertEqual(JSONHelper.convert_dict_to_json(12), 12)

        dict_ = JSONDict({"hello": 123, "numpy": NaN, "inf": inf, "a": ATest(a_test="hello")})
        self.assertEqual(
            dict_.default_view(ConfigParams()).data_to_dict(ConfigParams()),
            {"hello": 123, "numpy": None, "inf": None, "a": "hello"},
        )

    def test_extract_json_structure(self):
        # Sample JSON data
        json_data = {
            "name": "John",
            "age": 30,
            "float": 1.2,
            "none": None,
            "address": {"street": "123 Main St", "city": "New York"},
            "scores": [{"street": "123 Main St", "city": "New York"}],
        }

        # Extract the JSON structure
        json_structure = JSONHelper.extract_json_structure(json_data)

        result = {
            "name": "str",
            "age": "int",
            "float": "float",
            "none": "any",
            "address": {"street": "str", "city": "str"},
            "scores": [{"street": "str", "city": "str"}],
        }
        self.assert_json(json_structure, result)
