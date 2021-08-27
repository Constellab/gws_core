
from typing import Type

from gws_core import Model, Utils

from tests.base_test import BaseTest


class TestCSV(BaseTest):

    def test_get_model_type(self):
        model_type: Type[Model] = Utils.get_model_type(Model.full_classname())

        self.assertEqual(model_type, Model)
