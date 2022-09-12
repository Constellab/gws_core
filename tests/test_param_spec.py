# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import IsolatedAsyncioTestCase

from gws_core import IntParam, ParamSet, StrParam
from gws_core.config.param_spec_helper import ParamSpecHelper
from gws_core.core.utils.utils import Utils


# test_param_spec
class TestParamSpec(IsolatedAsyncioTestCase):

    def test_param_to_json(self):
        param: IntParam = IntParam(default_value=1, human_name="Test", short_description="Description",
                                   min_value=1, max_value=10, allowed_values=[1, 2], unit='km')
        dict_ = param.to_json()

        self.assertEqual(dict_["type"], "int")
        self.assertEqual(dict_["default_value"], 1)
        self.assertEqual(dict_["human_name"], "Test")
        self.assertEqual(dict_["short_description"], "Description")
        self.assertEqual(dict_["min_value"], 1)
        self.assertEqual(dict_["max_value"], 10)
        self.assertEqual(dict_["allowed_values"], [1, 2])
        self.assertEqual(dict_["unit"], "km")

    def test_param_set(self):
        param: ParamSet = ParamSet({"str": StrParam(), 'int': IntParam(default_value=12)}, max_number_of_occurrences=3)

        param_2: ParamSet = ParamSpecHelper.create_param_spec_from_json(param.to_json())
        self.assertIsInstance(param_2, ParamSet)
        self.assertEqual(param_2.max_number_of_occurrences, 3)
        self.assertIsInstance(param_2.param_set['str'], StrParam)
        self.assertIsInstance(param_2.param_set['int'], IntParam)

        # check the default value
        Utils.assert_json_equals(param_2.get_default_value(), [{'str': None, 'int': 12}])

        value = [{"str": "Hello", "int": "10"}]
        expected_value = [{"str": "Hello", "int": 10}]
        self.assertEqual(param.validate(value), expected_value)
