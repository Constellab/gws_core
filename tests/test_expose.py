# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import unittest
import json

from gws_core.core.utils.unittest import GTest
from gws_core.core.classes.expose import Expose
from gws_core.user.user import User
from gws_core.model.model_service import ModelService
from gws_core.user.user_service import UserService
from gws_core.resource.csv import CSVTable, CSVExporter, CSVImporter


class TestExpose(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    # def test_expose_models(self):
    #     GTest.print("Exposed models")

    #     def __expose__():
    #         """
    #         This is my test doc
    #         """

    #         return {
    #             ":CSV":{
    #                 "doc": "",
    #                 ":Data": {
    #                     "doc": "",
    #                     ":CSVData": {
    #                         "doc": "",
    #                         "type" : CSVData,
    #                     },
    #                 },

    #                 ":Process": {
    #                     "doc": "",
    #                     ":CSVImporter": {
    #                         "doc": "",
    #                         "type" : CSVImporter,
    #                     },
    #                     ":CSVExporter": {
    #                         "doc": "",
    #                         "type" : CSVExporter,
    #                     }
    #                 },
    #             }
    #         }

    #     parsed_data = Expose.analyze(__expose__)
    #     print(parsed_data)

    def test_expose_models_throuhg_model_service(self):
        GTest.print("Exposed models through model service")
        parsed_data = ModelService.get_exposed_models()
        print(json.dumps(parsed_data, indent=2))
