# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math
import unittest

from numpy import NaN

from gws_core import Validator
from gws_core.core.classes.validator import (BoolValidator, DictValidator,
                                             FloatValidator, IntValidator,
                                             ListValidator, StrValidator)


# test_validator
class TestValidator(unittest.TestCase):

    def test_int_validator(self):

        validator: Validator = IntValidator()
        self.assertEqual(validator.validate('3'), 3)
        self.assertEqual(validator.validate(3), 3)
        self.assertEqual(validator.validate(3.0), 3)
        self.assertRaises(Exception, validator.validate, 'false')
        self.assertRaises(Exception, validator.validate, 'true')
        self.assertRaises(Exception, validator.validate, 'foo')

        validator = IntValidator(allowed_values=[3, 5])
        self.assertRaises(Exception, validator.validate, 6)

    def test_str_validator(self):

        validator: Validator = StrValidator()
        self.assertEqual(validator.validate('4'), '4')
        self.assertEqual(validator.validate('false'), 'false')
        self.assertEqual(validator.validate('foo'), 'foo')
        self.assertRaises(Exception, validator.validate, 4)
        self.assertRaises(Exception, validator.validate, True)

    def test_bool_validator(self):

        validator: Validator = BoolValidator()
        self.assertEqual(validator.validate(False), False)
        self.assertEqual(validator.validate(True), True)
        self.assertEqual(validator.validate('true'), True)
        self.assertEqual(validator.validate('false'), False)
        self.assertRaises(Exception, validator.validate, 'foo')
        self.assertRaises(Exception, validator.validate, 4)

    def test_float_validator(self):

        validator: Validator = FloatValidator()
        self.assertEqual(validator.validate(5.5), 5.5)
        self.assertEqual(validator.validate(4.0), 4.0)
        self.assertEqual(validator.validate(4), 4.0)
        self.assertEqual(validator.validate('4'), 4.0)
        self.assertEqual(validator.validate('4.8'), 4.8)
        self.assertEqual(validator.validate('-4.8'), -4.8)
        self.assertEqual(validator.validate(-7), -7.0)
        self.assertEqual(validator.validate(math.inf), math.inf)
        self.assertEqual(validator.validate('Infinity'), math.inf)
        self.assertEqual(validator.validate('-Infinity'), -math.inf)
        self.assertTrue(math.isnan(validator.validate('NaN')))

        self.assertRaises(Exception, validator.validate, 'oui')
        self.assertRaises(Exception, validator.validate, True)
        self.assertRaises(Exception, validator.validate, 'false')
        self.assertRaises(Exception, validator.validate, '[1,3]')

        # min constaint
        validator = FloatValidator(min_value=-5)
        self.assertEqual(validator.validate('-4.8'), -4.8)
        self.assertRaises(Exception, validator.validate, '-7')

    def test_list_validator(self):

        validator: Validator = ListValidator()
        self.assertEqual(validator.validate([5.5, 3]), [5.5, 3])
        self.assertEqual(validator.validate('[5.5,3]'), [5.5, 3])
        self.assertEqual(validator.validate('[5.5,3,["foo","bar"]]'), [
                         5.5, 3, ["foo", "bar"]])
        self.assertEqual(validator.validate('[5.5,3,{"foo":1.2}]'), [
                         5.5, 3, {"foo": 1.2}])
        self.assertRaises(Exception, validator.validate, 'oui')
        self.assertRaises(Exception, validator.validate, True)
        self.assertRaises(Exception, validator.validate, 'false')
        self.assertRaises(Exception, validator.validate, '5.5')
        self.assertRaises(Exception, validator.validate, '{"foo":1.2}')

    def test_dict_validator(self):

        validator: Validator = DictValidator()
        self.assertEqual(validator.validate('{"foo":0.5}'), {"foo": 0.5})
        self.assertRaises(Exception, validator.validate, 'oui')
        self.assertRaises(Exception, validator.validate, True)
        self.assertRaises(Exception, validator.validate, 'false')
        self.assertRaises(Exception, validator.validate, '5.5')
        self.assertRaises(Exception, validator.validate, [5.5, 3])
        self.assertRaises(Exception, validator.validate, '[5.5,3]')
