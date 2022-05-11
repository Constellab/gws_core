
from typing import Literal, Set, Type

from gws_core import BaseTestCase, Model, Utils

literalType = Literal['one', 'two']


class TestUtils(BaseTestCase):

    def test_get_model_type(self):
        model_type: Type[Model] = Utils.get_model_type(Model.full_classname())

        self.assertEqual(model_type, Model)

    def test_value_is_in_literal(self):
        self.assertTrue(Utils.value_is_in_literal('one', literalType))
        self.assertFalse(Utils.value_is_in_literal('three', literalType))

    def test_get_subclasses(self):
        types: Set[Type[Model]] = Utils.get_all_subclasses(Model)

        self.assertTrue(len(types) > 0)
        for type_ in types:
            self.assertTrue(issubclass(type_, Model))

    def test_camel_to_sentence(self):
        self.assertEqual(Utils.camel_case_to_sentence('TestClassBuild'), 'Test class build')
        self.assertEqual(Utils.camel_case_to_sentence('TestClass2Build'), 'Test class2 build')
        self.assertEqual(Utils.camel_case_to_sentence('TestClass2 Build'), 'Test class2 build')

    def test_snake_case_to_sentence(self):
        self.assertEqual(Utils.snake_case_to_sentence('test_un'), 'Test un')
        self.assertEqual(Utils.snake_case_to_sentence('test _1'), 'Test 1')

    def test_str_is_alphanumeric(self):
        self.assertTrue(Utils.str_is_alphanumeric('test_12'))
        self.assertFalse(Utils.str_is_alphanumeric('test_.12'))
