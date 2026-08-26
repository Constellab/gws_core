import math
import unittest

from gws_core import Validator
from gws_core.core.classes.validator import (
    BoolValidator,
    DictValidator,
    FloatValidator,
    IntValidator,
    ListValidator,
    StrValidator,
)
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)


# test_validator
class TestValidator(unittest.TestCase):
    def test_int_validator(self):
        validator: Validator = IntValidator()
        self.assertEqual(validator.validate("3"), 3)
        self.assertEqual(validator.validate(3), 3)
        self.assertEqual(validator.validate(3.0), 3)
        self.assertRaises(BadRequestException, validator.validate, "false")
        self.assertRaises(BadRequestException, validator.validate, "true")
        self.assertRaises(BadRequestException, validator.validate, "foo")

        validator = IntValidator(allowed_values=[3, 5])
        self.assertRaises(BadRequestException, validator.validate, 6)

    def test_str_validator(self):
        validator: Validator = StrValidator()
        self.assertEqual(validator.validate("4"), "4")
        self.assertEqual(validator.validate("false"), "false")
        self.assertEqual(validator.validate("foo"), "foo")
        self.assertRaises(BadRequestException, validator.validate, 4)
        self.assertRaises(BadRequestException, validator.validate, True)

    def test_str_validator_regex(self):
        validator: Validator = StrValidator(regex="[A-Z]{3}")
        self.assertEqual(validator.validate("ABC"), "ABC")
        # fullmatch: a partial match is rejected
        self.assertRaises(BadRequestException, validator.validate, "ABCD")
        self.assertRaises(BadRequestException, validator.validate, "abc")

        # an invalid pattern raises on construction
        self.assertRaises(BadRequestException, StrValidator, regex="[A-Z")

        # the human-readable description is surfaced in the error message
        validator = StrValidator(regex="[A-Z]{3}", regex_description="three uppercase letters")
        try:
            validator.validate("abc")
            self.fail("Expected a validation error")
        except Exception as err:
            self.assertIn("three uppercase letters", str(err))

    def test_bool_validator(self):
        validator: Validator = BoolValidator()
        self.assertEqual(validator.validate(False), False)
        self.assertEqual(validator.validate(True), True)
        self.assertEqual(validator.validate("true"), True)
        self.assertEqual(validator.validate("false"), False)
        self.assertRaises(BadRequestException, validator.validate, "foo")
        self.assertRaises(BadRequestException, validator.validate, 4)

    def test_float_validator(self):
        validator: Validator = FloatValidator()
        self.assertEqual(validator.validate(5.5), 5.5)
        self.assertEqual(validator.validate(4.0), 4.0)
        self.assertEqual(validator.validate(4), 4.0)
        self.assertEqual(validator.validate("4"), 4.0)
        self.assertEqual(validator.validate("4.8"), 4.8)
        self.assertEqual(validator.validate("-4.8"), -4.8)
        self.assertEqual(validator.validate(-7), -7.0)
        self.assertEqual(validator.validate(math.inf), math.inf)
        self.assertEqual(validator.validate("Infinity"), math.inf)
        self.assertEqual(validator.validate("-Infinity"), -math.inf)
        self.assertTrue(math.isnan(validator.validate("NaN")))

        self.assertRaises(BadRequestException, validator.validate, "oui")
        self.assertRaises(BadRequestException, validator.validate, True)
        self.assertRaises(BadRequestException, validator.validate, "false")
        self.assertRaises(BadRequestException, validator.validate, "[1,3]")

        # min constaint
        validator = FloatValidator(min_value=-5)
        self.assertEqual(validator.validate("-4.8"), -4.8)
        self.assertRaises(BadRequestException, validator.validate, "-7")

    def test_list_validator(self):
        validator: Validator = ListValidator()
        self.assertEqual(validator.validate([5.5, 3]), [5.5, 3])
        self.assertEqual(validator.validate("[5.5,3]"), [5.5, 3])
        self.assertEqual(validator.validate('[5.5,3,["foo","bar"]]'), [5.5, 3, ["foo", "bar"]])
        self.assertEqual(validator.validate('[5.5,3,{"foo":1.2}]'), [5.5, 3, {"foo": 1.2}])
        self.assertRaises(BadRequestException, validator.validate, "oui")
        self.assertRaises(BadRequestException, validator.validate, True)
        self.assertRaises(BadRequestException, validator.validate, "false")
        self.assertRaises(BadRequestException, validator.validate, "5.5")
        self.assertRaises(BadRequestException, validator.validate, '{"foo":1.2}')

    def test_dict_validator(self):
        validator: Validator = DictValidator()
        self.assertEqual(validator.validate('{"foo":0.5}'), {"foo": 0.5})
        self.assertRaises(BadRequestException, validator.validate, "oui")
        self.assertRaises(BadRequestException, validator.validate, True)
        self.assertRaises(BadRequestException, validator.validate, "false")
        self.assertRaises(BadRequestException, validator.validate, "5.5")
        self.assertRaises(BadRequestException, validator.validate, [5.5, 3])
        self.assertRaises(BadRequestException, validator.validate, "[5.5,3]")
