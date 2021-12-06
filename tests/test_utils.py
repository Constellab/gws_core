
from typing import Set, Type

from gws_core import BaseTestCase, Model, Utils


class TestUtils(BaseTestCase):

    def test_get_model_type(self):
        model_type: Type[Model] = Utils.get_model_type(Model.full_classname())

        self.assertEqual(model_type, Model)

    def test_get_subclasses(self):
        types: Set[Type[Model]] = Utils.get_all_subclasses(Model)

        self.assertTrue(len(types) > 0)
        for type_ in types:
            self.assertTrue(issubclass(type_, Model))
