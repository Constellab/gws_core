# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math
import unittest

from gws_core import GTest, Validator
from gws_core.core.classes.validator import (BoolValidator, DictValidator,
                                             FloatValidator, IntValidator,
                                             ListValidator, StrValidator)


class TestValidator(unittest.TestCase):

    def test_int_validator(self):
        GTest.print("Integrer Validator")

        validator: Validator = IntValidator(default_value='5')
        self.assertEqual(validator.validate('3'), 3)
        self.assertEqual(validator.validate(3), 3)
        self.assertEqual(validator.validate(3.0), 3)
        self.assertEqual(validator.validate(None), 5)
        self.assertRaises(Exception, validator.validate, 'false')
        self.assertRaises(Exception, validator.validate, 'true')
        self.assertRaises(Exception, validator.validate, 'foo')

        validator = IntValidator(default_value='3.0')
        self.assertEqual(validator.validate(None), 3)

        validator = IntValidator(default_value='3.0', allowed_values=[3, 5])
        self.assertEqual(validator.validate(None), 3)
        self.assertRaises(Exception, validator.validate, 6)

        # invalid validator
        self.assertRaises(Exception, IntValidator, default_value='5.5')
        self.assertRaises(Exception, IntValidator, default_value='oui')
        self.assertRaises(Exception, IntValidator, default_value='"oui"')

    def test_str_validator(self):
        GTest.print("String Validator")

        validator: Validator = StrValidator(default_value='5')
        self.assertEqual(validator.validate('4'), '4')
        self.assertEqual(validator.validate(None), '5')
        self.assertEqual(validator.validate('false'), 'false')
        self.assertEqual(validator.validate('foo'), 'foo')
        self.assertRaises(Exception, validator.validate, 4)
        self.assertRaises(Exception, validator.validate, True)

        # invalid validator
        self.assertRaises(Exception, StrValidator,  default_value=5)
        self.assertRaises(Exception, StrValidator,  default_value=True)

    def test_bool_validator(self):
        GTest.print("Boolean Validator")

        validator: Validator = BoolValidator(default_value=True)
        self.assertEqual(validator.validate(False), False)
        self.assertEqual(validator.validate(True), True)
        self.assertEqual(validator.validate(None), True)
        self.assertEqual(validator.validate('true'), True)
        self.assertEqual(validator.validate('false'), False)
        self.assertRaises(Exception, validator.validate, 'foo')
        self.assertRaises(Exception, validator.validate, 4)

        validator = BoolValidator(default_value='true')
        self.assertEqual(validator.validate(None), True)

        validator = BoolValidator()
        self.assertEqual(validator.validate(None), None)

        # invalid validator
        self.assertRaises(Exception, BoolValidator, default_value='foo')
        self.assertRaises(Exception, BoolValidator, default_value=0)

    def test_float_validator(self):
        GTest.print("Float Validator")

        validator: Validator = FloatValidator(default_value='8')
        self.assertEqual(validator.validate(5.5), 5.5)
        self.assertEqual(validator.validate(4.0), 4.0)
        self.assertEqual(validator.validate(4), 4.0)
        self.assertEqual(validator.validate('4'), 4.0)
        self.assertEqual(validator.validate('4.8'), 4.8)
        self.assertEqual(validator.validate('-4.8'), -4.8)
        self.assertEqual(validator.validate(-7), -7.0)
        self.assertEqual(validator.validate(None), 8)
        self.assertEqual(validator.validate(math.inf), math.inf)
        self.assertEqual(validator.validate('Infinity'), math.inf)
        self.assertEqual(validator.validate('-Infinity'), -math.inf)
        self.assertTrue(math.isnan(validator.validate('NaN')))

        self.assertRaises(Exception, validator.validate, 'oui')
        self.assertRaises(Exception, validator.validate, True)
        self.assertRaises(Exception, validator.validate, 'false')
        self.assertRaises(Exception, validator.validate, '[1,3]')

        # invalid validator
        self.assertRaises(Exception, FloatValidator, default_value='foo')

        # min constaint
        validator = FloatValidator(default_value='8', min_value=-5)
        self.assertEqual(validator.validate('-4.8'), -4.8)
        self.assertRaises(Exception, validator.validate, '-7')

    def test_list_validator(self):
        GTest.print("List Validator")

        validator: Validator = ListValidator(default_value='[1,2,"foo"]')
        self.assertEqual(validator.validate([5.5, 3]), [5.5, 3])
        self.assertEqual(validator.validate('[5.5,3]'), [5.5, 3])
        self.assertEqual(validator.validate('[5.5,3,["foo","bar"]]'), [
                         5.5, 3, ["foo", "bar"]])
        self.assertEqual(validator.validate('[5.5,3,{"foo":1.2}]'), [
                         5.5, 3, {"foo": 1.2}])
        self.assertEqual(validator.validate(None), [1, 2, "foo"])
        self.assertRaises(Exception, validator.validate, 'oui')
        self.assertRaises(Exception, validator.validate, True)
        self.assertRaises(Exception, validator.validate, 'false')
        self.assertRaises(Exception, validator.validate, '5.5')
        self.assertRaises(Exception, validator.validate, '{"foo":1.2}')

        # invalid validator
        self.assertRaises(Exception, ListValidator, default_value='foo')
        self.assertRaises(Exception, ListValidator, default_value=True)

    def test_dict_validator(self):
        GTest.print("Dict Validator")

        validator: Validator = DictValidator(default_value='{"foo":1.2}')
        self.assertEqual(validator.validate(None), {"foo": 1.2})
        self.assertEqual(validator.validate('{"foo":0.5}'), {"foo": 0.5})
        self.assertRaises(Exception, validator.validate, 'oui')
        self.assertRaises(Exception, validator.validate, True)
        self.assertRaises(Exception, validator.validate, 'false')
        self.assertRaises(Exception, validator.validate, '5.5')
        self.assertRaises(Exception, validator.validate, [5.5, 3])
        self.assertRaises(Exception, validator.validate, '[5.5,3]')

        # invalid validator
        self.assertRaises(Exception, DictValidator, default_value='foo')
        self.assertRaises(Exception, DictValidator, default_value=True)
