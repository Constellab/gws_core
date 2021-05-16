# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import unittest
from gws.validator import Validator
from gws.logger import Error

class TestValidator(unittest.TestCase):

    def test_int_validator(self):
        v = Validator.from_specs(type='int', default='5')
        self.assertEqual(v.validate('3'), 3)
        self.assertEqual(v.validate(3), 3)
        self.assertEqual(v.validate(3.0), 3)
        self.assertEqual(v.validate(None), 5)
        self.assertRaises(Error, v.validate, 'false')
        self.assertRaises(Error, v.validate, 'true')
        self.assertRaises(Error, v.validate, 'foo')

        v = Validator.from_specs(type=int, default='3.0')
        self.assertEqual(v.validate(None), 3)

        v = Validator.from_specs(type=int, default='3.0', allowed_values=[3, 5])
        self.assertEqual(v.validate(None), 3)
        self.assertRaises(Error, v.validate, 6)
    
        #invalid validator
        self.assertRaises(Error, Validator.from_specs, type=int, default='5.5')
        self.assertRaises(Error, Validator.from_specs, type=int, default='oui')
        self.assertRaises(Error, Validator.from_specs, type=int, default='"oui"')
        #self.assertRaises(Error, Validator.from_specs, type=int, default=3, allowed_values=[10, 12])



    def test_str_validator(self):
        v = Validator.from_specs(type='str', default='5')
        self.assertEqual(v.validate('4'), '4')
        self.assertEqual(v.validate(None), '5')
        self.assertEqual(v.validate('false'), 'false')
        self.assertEqual(v.validate('foo'), 'foo')
        self.assertRaises(Error, v.validate, 4)
        self.assertRaises(Error, v.validate, True)

        #invalid validator
        self.assertRaises(Error, Validator.from_specs, type=str, default=5)
        self.assertRaises(Error, Validator.from_specs, type=str, default=True)

    def test_bool_validator(self):
        v = Validator.from_specs(type=bool, default=True)
        self.assertEqual(v.validate(False), False)
        self.assertEqual(v.validate(True), True)
        self.assertEqual(v.validate(None), True)
        self.assertEqual(v.validate('true'), True)
        self.assertEqual(v.validate('false'), False)
        self.assertRaises(Error, v.validate, 'foo')
        self.assertRaises(Error, v.validate, 4)

        v = Validator.from_specs(type='bool', default='true')
        self.assertEqual(v.validate(None), True)

        v = Validator.from_specs(type=bool)
        self.assertEqual(v.validate(None), None)

        #invalid validator
        self.assertRaises(Error, Validator.from_specs, type=bool, default='foo')
        self.assertRaises(Error, Validator.from_specs, type=bool, default=0)

    def test_float_validator(self):
        import math

        v = Validator.from_specs(type=float, default='8')
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

        self.assertRaises(Error, v.validate, 'oui')
        self.assertRaises(Error, v.validate, True)
        self.assertRaises(Error, v.validate, 'false')
        self.assertRaises(Error, v.validate, '[1,3]')

        #invalid validator
        self.assertRaises(Error, Validator.from_specs, type='float', default='foo')

        #min constaint
        v = Validator.from_specs(type=float, default='8', min=-5)
        self.assertEqual(v.validate('-4.8'), -4.8)
        self.assertRaises(Error, v.validate, '-7')

    def test_list_validator(self):
        v = Validator.from_specs(type='list', default='[1,2,"foo"]')
        self.assertEqual(v.validate([5.5,3]), [5.5,3])
        self.assertEqual(v.validate('[5.5,3]'), [5.5,3])
        self.assertEqual(v.validate('[5.5,3,["foo","bar"]]'), [5.5,3,["foo","bar"]])
        self.assertEqual(v.validate('[5.5,3,{"foo":1.2}]'), [5.5,3,{"foo":1.2}])
        self.assertEqual(v.validate(None), [1,2,"foo"])
        self.assertRaises(Error, v.validate, 'oui')
        self.assertRaises(Error, v.validate, True)
        self.assertRaises(Error, v.validate, 'false')
        self.assertRaises(Error, v.validate, '5.5')
        self.assertRaises(Error, v.validate, '{"foo":1.2}')

        #invalid validator
        self.assertRaises(Error, Validator.from_specs, type=list, default='foo')
        self.assertRaises(Error, Validator.from_specs, type=list, default=True)

    def test_dict_validator(self):
        v = Validator.from_specs(type='dict', default='{"foo":1.2}')
        self.assertEqual(v.validate(None), {"foo":1.2})
        self.assertEqual(v.validate('{"foo":0.5}'), {"foo":0.5})
        self.assertRaises(Error, v.validate, 'oui')
        self.assertRaises(Error, v.validate, True)
        self.assertRaises(Error, v.validate, 'false')
        self.assertRaises(Error, v.validate, '5.5')
        self.assertRaises(Error, v.validate, [5.5,3])
        self.assertRaises(Error, v.validate, '[5.5,3]')

        #invalid validator
        self.assertRaises(Error, Validator.from_specs, type=list, default='foo')
        self.assertRaises(Error, Validator.from_specs, type=list, default=True)
