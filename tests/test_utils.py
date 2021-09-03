
from typing import Type

from gws_core import BaseTestCase, Model, Utils


class TestCSV(BaseTestCase):

    def test_get_model_type(self):
        model_type: Type[Model] = Utils.get_model_type(Model.full_classname())

        self.assertEqual(model_type, Model)
