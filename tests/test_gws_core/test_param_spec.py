

from unittest import TestCase

from gws_core import IntParam, ParamSet, StrParam
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.config.param.param_types import ParamSpecTypeStr
from gws_core.core.utils.utils import Utils


# test_param_spec
class TestParamSpec(TestCase):

    def test_param_to_json(self):
        param = IntParam(default_value=1, human_name="Test", short_description="Description",
                         min_value=1, max_value=10, allowed_values=[1, 2])

        spec_dto = param.to_dto()

        self.assertEqual(spec_dto.type, ParamSpecTypeStr.INT)
        self.assertEqual(spec_dto.default_value, 1)
        self.assertEqual(spec_dto.human_name, "Test")
        self.assertEqual(spec_dto.short_description, "Description")
        self.assertEqual(spec_dto.additional_info["min_value"], 1)
        self.assertEqual(spec_dto.additional_info["max_value"], 10)
        self.assertEqual(spec_dto.additional_info["allowed_values"], [1, 2])

    def test_param_set(self):
        param = ParamSet({"str": StrParam(), 'int': IntParam(default_value=12)}, max_number_of_occurrences=3)

        param_2: ParamSet = ParamSpecHelper.create_param_spec_from_json(param.to_dto())
        self.assertIsInstance(param_2, ParamSet)
        self.assertEqual(param_2.max_number_of_occurrences, 3)
        self.assertIsInstance(param_2.param_set['str'], StrParam)
        self.assertIsInstance(param_2.param_set['int'], IntParam)

        # check the default value
        Utils.assert_json_equals(param_2.get_default_value(), [{'str': None, 'int': 12}])

        value = [{"str": "Hello", "int": "10"}]
        expected_value = [{"str": "Hello", "int": 10}]
        self.assertEqual(param.validate(value), expected_value)
