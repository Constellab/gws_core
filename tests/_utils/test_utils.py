# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Literal, Set, Type
from unittest import IsolatedAsyncioTestCase

from gws_core import Model, Utils

LiteralType = Literal['one', 'two']


class SubString(str):
    pass


class TestUtils(IsolatedAsyncioTestCase):

    def test_get_model_type(self):
        model_type: Type[Model] = Utils.get_model_type(Model.full_classname())

        self.assertEqual(model_type, Model)

    def test_value_is_in_literal(self):
        self.assertTrue(Utils.value_is_in_literal('one', LiteralType))
        self.assertFalse(Utils.value_is_in_literal('three', LiteralType))

    def test_get_subclasses(self):
        types: Set[Type[Model]] = Utils.get_all_subclasses(Model)

        self.assertTrue(len(types) > 0)
        for type_ in types:
            self.assertTrue(issubclass(type_, Model))

    def test_uniquify_str_list(self):
        self.assertEqual(Utils.rename_duplicate_in_str_list(['A', 'B', 'A', 'B', 'A', 'A_1']),
                         ['A', 'B', 'A_1', 'B_1', 'A_2', 'A_1_1'])

    def test_is_primitive(self):
        self.assertTrue(Utils.is_primitive(1))
        self.assertTrue(Utils.is_primitive('1'))
        self.assertTrue(Utils.is_primitive(1.0))
        self.assertTrue(Utils.is_primitive(False))
        self.assertFalse(Utils.is_primitive(SubString('1')))

    def test_is_json(self):
        self.assertTrue(Utils.is_json(1))
        self.assertTrue(Utils.is_json('1'))
        self.assertTrue(Utils.is_json(1.0))
        self.assertTrue(Utils.is_json(False))
        self.assertFalse(Utils.is_json(SubString('1')))

        self.assertTrue(Utils.is_json({"a": ['1', '2', {'test': 'Super'}]}))
        self.assertFalse(Utils.is_json({"a": ['1', '2', {'test': SubString('1')}]}))
