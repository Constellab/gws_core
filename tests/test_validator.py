
import asyncio
import unittest
from gws.validator import Validator

class TestValidator(unittest.TestCase):

    def test_int_validator(self):
        v = Validator.from_type(int, default='5')
        self.assertEqual(v.validate('3'), 3)
        self.assertEqual(v.validate(3), 3)
        self.assertEqual(v.validate(3.0), 3)
        self.assertEqual(v.validate(None), 5)
        self.assertRaises(ValueError, v.validate, 'false')
        self.assertRaises(ValueError, v.validate, 'true')
        self.assertRaises(ValueError, v.validate, 'foo')

        v = Validator.from_type(int, default='3.0')
        self.assertEqual(v.validate(None), 3)
    
        #invalid validator
        self.assertRaises(Exception, Validator.from_type, int, default='5.5')
        self.assertRaises(Exception, Validator.from_type, int, default='oui')
        self.assertRaises(Exception, Validator.from_type, int, default='"oui"')

        

    def test_str_validator(self):
        v = Validator.from_type(str, default='5')
        self.assertEqual(v.validate('4'), '4')
        self.assertEqual(v.validate(None), '5')
        self.assertEqual(v.validate('false'), 'false')
        self.assertEqual(v.validate('foo'), 'foo')
        self.assertRaises(ValueError, v.validate, 4)
        self.assertRaises(ValueError, v.validate, True)

        #invalid validator
        self.assertRaises(Exception, Validator.from_type, str, default=5)
        self.assertRaises(Exception, Validator.from_type, str, default=True)

    def test_bool_validator(self):
        v = Validator.from_type(bool, default=True)
        self.assertEqual(v.validate(False), False)
        self.assertEqual(v.validate(True), True)
        self.assertEqual(v.validate(None), True)
        self.assertEqual(v.validate('true'), True)
        self.assertEqual(v.validate('false'), False)
        self.assertRaises(ValueError, v.validate, 'foo')
        self.assertRaises(ValueError, v.validate, 4)

        v = Validator.from_type(bool, default='true')
        self.assertEqual(v.validate(None), True)

        v = Validator.from_type(bool)
        self.assertEqual(v.validate(None), None)

        #invalid validator
        self.assertRaises(Exception, Validator.from_type, bool, default='foo')
        self.assertRaises(Exception, Validator.from_type, bool, default=0)

    def test_float_validator(self):
        import math

        v = Validator.from_type(float, default='8')
        self.assertEqual(v.validate(5.5), 5.5)
        self.assertEqual(v.validate(4.0), 4.0)
        self.assertEqual(v.validate(4), 4.0)
        self.assertEqual(v.validate('4'), 4.0)
        self.assertEqual(v.validate('4.8'), 4.8)
        self.assertEqual(v.validate('-4.8'), -4.8)
        self.assertEqual(v.validate(-7), -7.0)
        self.assertEqual(v.validate(None), 8)
        self.assertEqual(v.validate(math.inf), math.inf)
        self.assertEqual(v.validate('Infinity'), math.inf)
        self.assertEqual(v.validate('-Infinity'), -math.inf)
        self.assertTrue(math.isnan(v.validate('NaN')))

        self.assertRaises(ValueError, v.validate, 'oui')
        self.assertRaises(ValueError, v.validate, True)
        self.assertRaises(ValueError, v.validate, 'false')
        self.assertRaises(ValueError, v.validate, '[1,3]')

        #invalid validator
        self.assertRaises(Exception, Validator.from_type, float, default='foo')

        #min constaint
        v = Validator.from_type(float, default='8', min=-5)
        self.assertEqual(v.validate('-4.8'), -4.8)
        self.assertRaises(ValueError, v.validate, '-7')

    def test_list_validator(self):
        v = Validator.from_type(list, default='[1,2,"foo"]')
        self.assertEqual(v.validate([5.5,3]), [5.5,3])
        self.assertEqual(v.validate('[5.5,3]'), [5.5,3])
        self.assertEqual(v.validate('[5.5,3,["foo","bar"]]'), [5.5,3,["foo","bar"]])
        self.assertEqual(v.validate('[5.5,3,{"foo":1.2}]'), [5.5,3,{"foo":1.2}])
        self.assertEqual(v.validate(None), [1,2,"foo"])
        self.assertRaises(ValueError, v.validate, 'oui')
        self.assertRaises(ValueError, v.validate, True)
        self.assertRaises(ValueError, v.validate, 'false')
        self.assertRaises(ValueError, v.validate, '5.5')
        self.assertRaises(ValueError, v.validate, '{"foo":1.2}')

        #invalid validator
        self.assertRaises(Exception, Validator.from_type, list, default='foo')
        self.assertRaises(Exception, Validator.from_type, list, default=True)

    def test_dict_validator(self):
        v = Validator.from_type(dict, default='{"foo":1.2}')
        self.assertEqual(v.validate(None), {"foo":1.2})
        self.assertEqual(v.validate('{"foo":0.5}'), {"foo":0.5})
        self.assertRaises(ValueError, v.validate, 'oui')
        self.assertRaises(ValueError, v.validate, True)
        self.assertRaises(ValueError, v.validate, 'false')
        self.assertRaises(ValueError, v.validate, '5.5')
        self.assertRaises(ValueError, v.validate, [5.5,3])
        self.assertRaises(ValueError, v.validate, '[5.5,3]')

        #invalid validator
        self.assertRaises(Exception, Validator.from_type, list, default='foo')
        self.assertRaises(Exception, Validator.from_type, list, default=True)
