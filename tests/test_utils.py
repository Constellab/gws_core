
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

    def test_camel_to_sentence(self):
        self.assertEqual(Utils.camel_case_to_sentence('TestClassBuild'), 'Test class build')
        self.assertEqual(Utils.camel_case_to_sentence('TestClass2Build'), 'Test class2 build')
        self.assertEqual(Utils.camel_case_to_sentence('TestClass2 Build'), 'Test class2 build')
