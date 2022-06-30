# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Literal, Set, Type
from unittest import IsolatedAsyncioTestCase

from gws_core import Model, Utils

LiteralType = Literal['one', 'two']


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
