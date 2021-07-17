# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import unittest
from gws.service.model_service import ModelService
from gws.service.process_service import ProcessService
from gws.service.protocol_service import ProtocolService
from gws.unittest import GTest

class TestTyping(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()
        ModelService.register_all_processes_and_resources()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_typing(self):
        GTest.print("Model Typing")

        _json = ProcessService.fetch_process_type_list(as_json=True)
        self.assertTrue(len(_json["data"]) > 0)
        #print("\n------- fetch_process_type_list -------\n")
        #print(_json["data"][0])

        _json = ProtocolService.fetch_protocol_type_list(as_json=True)
        self.assertTrue(len(_json["data"]) > 0)
        #print("\n------- fetch_protocol_type_list -------\n")
        #print(_json["data"][0])


        