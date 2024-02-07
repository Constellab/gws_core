# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from unittest import TestCase

from gws_core import StringHelper


class SimpleEnum(Enum):
    TEST_1 = "TEST_1"


# test_string_helper
class TestStringHelper(TestCase):

    def test_camel_to_sentence(self):
        self.assertEqual(StringHelper.camel_case_to_sentence('TestClassBuild'), 'Test class build')
        self.assertEqual(StringHelper.camel_case_to_sentence('TestClass2Build'), 'Test class2 build')
        self.assertEqual(StringHelper.camel_case_to_sentence('TestClass2 Build'), 'Test class2 build')

    def test_snake_case_to_sentence(self):
        self.assertEqual(StringHelper.snake_case_to_sentence('test_un'), 'Test un')
        self.assertEqual(StringHelper.snake_case_to_sentence('test _1'), 'Test 1')

    def test_str_is_alphanumeric(self):
        self.assertTrue(StringHelper.is_alphanumeric('test_12'))
        self.assertFalse(StringHelper.is_alphanumeric('test_.12'))

    def test_remove_whitespace(self):
        self.assertEqual(StringHelper.remove_whitespaces(' test  _1\n2 '), 'test_12')

    def test_str_to_enum(self):
        self.assertEqual(StringHelper.to_enum(SimpleEnum, 'TEST_1'), SimpleEnum.TEST_1)

    def test_replace_accents(self):
        self.assertEqual(StringHelper.replace_accent_with_letter('àéèïìòùÉÊ'), 'aeeiiouEE')
