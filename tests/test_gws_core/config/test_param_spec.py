from datetime import date, datetime
from unittest import TestCase

from gws_core import DateParam, IntParam, ParamSet, SelectParam, StrParam
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.code_param.json_code_param import JsonCodeParam
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.config.param.param_types import ParamSpecType
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.utils.utils import Utils


# test_param_spec
class TestParamSpec(TestCase):
    def test_param_to_json(self):
        param = IntParam(
            default_value=1,
            human_name="Test",
            short_description="Description",
            min_value=1,
            max_value=10,
            allowed_values=[1, 2],
        )

        spec_dto = param.to_dto()

        self.assertEqual(spec_dto.type, ParamSpecType.INT)
        self.assertEqual(spec_dto.default_value, 1)
        self.assertEqual(spec_dto.human_name, "Test")
        self.assertEqual(spec_dto.short_description, "Description")
        self.assertEqual(spec_dto.additional_info["min_value"], 1)
        self.assertEqual(spec_dto.additional_info["max_value"], 10)
        self.assertEqual(spec_dto.additional_info["allowed_values"], [1, 2])

    def test_param_set(self):
        param = ParamSet(
            ConfigSpecs({"str": StrParam(), "int": IntParam(default_value=12)}),
            max_number_of_occurrences=3,
        )

        param_2: ParamSet = ParamSpecHelper.create_param_spec_from_json(param.to_dto())
        self.assertIsInstance(param_2, ParamSet)
        self.assertEqual(param_2.max_number_of_occurrences, 3)
        self.assertIsInstance(param_2.param_set.get_spec("str"), StrParam)
        self.assertIsInstance(param_2.param_set.get_spec("int"), IntParam)

        # check the default value
        Utils.assert_json_equals(param_2.get_default_value(), [{"str": None, "int": 12}])

        # ParamSet.validate mints a __item_id per row; assert on the inner
        # fields rather than full-dict equality.
        value = [{"str": "Hello", "int": "10"}]
        validated = param.validate(value)
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0]["str"], "Hello")
        self.assertEqual(validated[0]["int"], 10)
        self.assertIn(ConfigSpecs.ITEM_ID_KEY, validated[0])

    def test_select_param(self):
        param = SelectParam(
            options=["a", "b", "c"],
            default_value="a",
            human_name="Select",
        )

        spec_dto = param.to_dto()
        self.assertEqual(spec_dto.type, ParamSpecType.SELECT)
        self.assertEqual(spec_dto.default_value, "a")
        self.assertFalse(spec_dto.additional_info["multiple"])
        self.assertEqual(
            spec_dto.additional_info["options"],
            [
                {"label": "a", "value": "a"},
                {"label": "b", "value": "b"},
                {"label": "c", "value": "c"},
            ],
        )

        self.assertEqual(param.validate("b"), "b")
        self.assertIsNone(param.validate(None))
        with self.assertRaises(BadRequestException):
            param.validate("zzz")

        # round trip
        param_2 = ParamSpecHelper.create_param_spec_from_json(spec_dto)
        self.assertIsInstance(param_2, SelectParam)
        self.assertEqual(param_2.additional_info, param.additional_info)

        # registration
        self.assertIs(
            ParamSpecHelper.get_param_spec_type_from_str(ParamSpecType.SELECT), SelectParam
        )

    def test_select_param_with_options(self):
        param = SelectParam(
            options=["a", {"label": "Bee", "value": "b"}],
            default_value="a",
        )

        self.assertEqual(
            param.additional_info["options"],
            [
                {"label": "a", "value": "a"},
                {"label": "Bee", "value": "b"},
            ],
        )
        # validation checks against the stored value, not the label
        self.assertEqual(param.validate("b"), "b")
        with self.assertRaises(BadRequestException):
            param.validate("Bee")

    def test_select_param_multiple(self):
        param = SelectParam(options=["a", "b", "c"], multiple=True)

        self.assertTrue(param.additional_info["multiple"])
        self.assertEqual(param.get_default_value(), [])
        self.assertTrue(param.optional)

        self.assertEqual(param.validate(["a", "c"]), ["a", "c"])
        with self.assertRaises(BadRequestException):
            param.validate(["a", "zzz"])
        with self.assertRaises(BadRequestException):
            param.validate("a")

        param_2 = ParamSpecHelper.create_param_spec_from_json(param.to_dto())
        self.assertIsInstance(param_2, SelectParam)
        self.assertTrue(param_2.additional_info["multiple"])

    def test_date_param(self):
        param = DateParam(
            default_value="2026-05-13",
            min_value="2020-01-01",
            max_value="2030-12-31",
            human_name="Birthday",
            short_description="When you were born",
        )

        spec_dto = param.to_dto()
        self.assertEqual(spec_dto.type, ParamSpecType.DATE)
        self.assertEqual(spec_dto.default_value, "2026-05-13")
        self.assertEqual(spec_dto.human_name, "Birthday")
        self.assertEqual(spec_dto.short_description, "When you were born")
        self.assertFalse(spec_dto.additional_info["include_time"])
        self.assertEqual(spec_dto.additional_info["min_value"], "2020-01-01")
        self.assertEqual(spec_dto.additional_info["max_value"], "2030-12-31")

        # validation: string in range
        self.assertEqual(param.validate("2025-06-15"), "2025-06-15")
        # None is allowed (param is optional via default_value)
        self.assertIsNone(param.validate(None))
        # date object accepted, normalized to ISO string
        self.assertEqual(param.validate(date(2025, 6, 15)), "2025-06-15")
        # datetime input is truncated to date when include_time is False
        self.assertEqual(param.validate(datetime(2025, 6, 15, 14, 30)), "2025-06-15")

        # out of range
        with self.assertRaises(BadRequestException):
            param.validate("2019-12-31")
        with self.assertRaises(BadRequestException):
            param.validate("2031-01-01")
        # bad format
        with self.assertRaises(BadRequestException):
            param.validate("not-a-date")
        # bad type
        with self.assertRaises(BadRequestException):
            param.validate(123)

        # round trip via the registry
        param_2 = ParamSpecHelper.create_param_spec_from_json(spec_dto)
        self.assertIsInstance(param_2, DateParam)
        self.assertEqual(param_2.additional_info, param.additional_info)
        self.assertEqual(param_2.default_value, param.default_value)

        # registration
        self.assertIs(
            ParamSpecHelper.get_param_spec_type_from_str(ParamSpecType.DATE), DateParam
        )

    def test_date_param_with_time(self):
        param = DateParam(
            include_time=True,
            default_value="2026-05-13T14:30:00",
            min_value=datetime(2020, 1, 1),
            max_value="2030-12-31T23:59:59",
        )

        self.assertTrue(param.additional_info["include_time"])
        self.assertEqual(param.additional_info["min_value"], "2020-01-01T00:00:00")
        self.assertEqual(param.additional_info["max_value"], "2030-12-31T23:59:59")
        self.assertEqual(param.default_value, "2026-05-13T14:30:00")

        # datetime object accepted
        self.assertEqual(
            param.validate(datetime(2025, 6, 15, 9, 0, 0)),
            "2025-06-15T09:00:00",
        )
        # date object promoted to midnight datetime
        self.assertEqual(param.validate(date(2025, 6, 15)), "2025-06-15T00:00:00")
        # a date-only string is accepted and promoted to midnight
        # (datetime.fromisoformat accepts date-only inputs)
        self.assertEqual(param.validate("2025-06-15"), "2025-06-15T00:00:00")
        # but a malformed string is still rejected
        with self.assertRaises(BadRequestException):
            param.validate("not-a-date")

        # round trip preserves include_time
        param_2 = ParamSpecHelper.create_param_spec_from_json(param.to_dto())
        self.assertIsInstance(param_2, DateParam)
        self.assertTrue(param_2.additional_info["include_time"])

    def test_date_param_build(self):
        # date mode: build returns a date
        param = DateParam(default_value="2026-05-13")
        built = param.build("2025-06-15")
        self.assertIsInstance(built, date)
        # specifically a date, not a datetime (datetime is a subclass of date)
        self.assertNotIsInstance(built, datetime)
        self.assertEqual(built, date(2025, 6, 15))
        self.assertIsNone(param.build(None))
        # idempotent on date / datetime inputs
        self.assertEqual(param.build(date(2025, 6, 15)), date(2025, 6, 15))
        self.assertEqual(param.build(datetime(2025, 6, 15, 10, 0)), date(2025, 6, 15))

        # datetime mode: build returns a datetime
        param_dt = DateParam(include_time=True, optional=True)
        built_dt = param_dt.build("2025-06-15T14:30:00")
        self.assertIsInstance(built_dt, datetime)
        self.assertEqual(built_dt, datetime(2025, 6, 15, 14, 30))
        # date input is promoted to midnight
        self.assertEqual(
            param_dt.build(date(2025, 6, 15)), datetime(2025, 6, 15, 0, 0)
        )

    def test_date_param_invalid_construction(self):
        # min > max should fail at construction time
        with self.assertRaises(BadRequestException):
            DateParam(min_value="2030-01-01", max_value="2020-01-01", optional=True)

        # default_value out of range should fail at construction time
        # (super().__init__ calls self.validate on the default)
        with self.assertRaises(BadRequestException):
            DateParam(default_value="2019-01-01", min_value="2020-01-01")

        # malformed min_value / max_value rejected at construction
        with self.assertRaises(BadRequestException):
            DateParam(min_value="not-a-date", optional=True)
        with self.assertRaises(BadRequestException):
            DateParam(max_value="2030-13-99", optional=True)
        with self.assertRaises(BadRequestException):
            DateParam(min_value=12345, optional=True)

    def test_date_param_load_from_dto_validates_bounds(self):
        from gws_core.config.param.param_types import ParamSpecDTO

        # a DTO carrying a malformed min_value should be rejected by load_from_dto
        # when validate=True (strict-write path used by callers that are about
        # to commit a fresh spec).
        bad_dto = ParamSpecDTO(
            type=ParamSpecType.DATE,
            optional=True,
            visibility="public",
            additional_info={
                "include_time": False,
                "min_value": "not-a-date",
                "max_value": None,
            },
            default_value=None,
        )
        with self.assertRaises(BadRequestException):
            DateParam.load_from_dto(bad_dto, validate=True)

        # min > max in a DTO is also rejected when validate=True
        bad_order_dto = ParamSpecDTO(
            type=ParamSpecType.DATE,
            optional=True,
            visibility="public",
            additional_info={
                "include_time": False,
                "min_value": "2030-01-01",
                "max_value": "2020-01-01",
            },
            default_value=None,
        )
        with self.assertRaises(BadRequestException):
            DateParam.load_from_dto(bad_order_dto, validate=True)

        # a well-formed DTO loads fine when validate=True
        good_dto = ParamSpecDTO(
            type=ParamSpecType.DATE,
            optional=True,
            visibility="public",
            additional_info={
                "include_time": False,
                "min_value": "2020-01-01",
                "max_value": "2030-12-31",
            },
            default_value="2025-06-15",
        )
        loaded = DateParam.load_from_dto(good_dto, validate=True)
        self.assertEqual(loaded.additional_info["min_value"], "2020-01-01")
        self.assertEqual(loaded.additional_info["max_value"], "2030-12-31")
        self.assertEqual(loaded.default_value, "2025-06-15")

    def test_date_param_load_from_dto_lenient(self):
        """Lenient-read path: a previously-persisted spec with a bad bound must
        still load so that read-modify-write operations (delete a field, reorder
        fields, view the form) keep working even when stored data is malformed.
        """
        from gws_core.config.param.param_types import ParamSpecDTO

        bad_dto = ParamSpecDTO(
            type=ParamSpecType.DATE,
            optional=True,
            visibility="public",
            additional_info={
                "include_time": False,
                "min_value": "not-a-date",
                "max_value": None,
            },
            default_value=None,
        )
        # Default validate=False: must not raise.
        loaded = DateParam.load_from_dto(bad_dto)
        self.assertEqual(loaded.additional_info["min_value"], "not-a-date")

        bad_order_dto = ParamSpecDTO(
            type=ParamSpecType.DATE,
            optional=True,
            visibility="public",
            additional_info={
                "include_time": False,
                "min_value": "2030-01-01",
                "max_value": "2020-01-01",
            },
            default_value=None,
        )
        loaded = DateParam.load_from_dto(bad_order_dto)
        self.assertEqual(loaded.additional_info["min_value"], "2030-01-01")
        self.assertEqual(loaded.additional_info["max_value"], "2020-01-01")

    def test_json_param(self):
        param = JsonCodeParam()

        result = param.build('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

        # test with comments
        json_with_comments = """
        {
            // This is a comment
            "key": "value // super"
        }
        """
        result = param.build(json_with_comments)
        self.assertEqual(result, {"key": "value // super"})
