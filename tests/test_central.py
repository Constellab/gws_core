import os
import unittest
import json

from gws.model import User, Experiment, Protocol
from gws.central import Central
from gws.settings import Settings
from gws.logger import Error

class TestCentral(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        User.drop_table()
        Experiment.drop_table()
        Protocol.drop_table()

    @classmethod
    def tearDownClass(cls):
        User.drop_table()
        Experiment.drop_table()
        Protocol.drop_table()

    def test_create_user(self):
        data = {
            "uri": "1234567890"
        }
        tf = Central.create_user(data)
        self.assertTrue(tf)
        user = User.get_by_uri("1234567890")
        self.assertEqual(user.uri, "1234567890")

    def test_create_experiment_exception(self):
        data = {
            "uri": "123456abcd",
            "protocol": {
                "uri": "1234ERTY",
            }
        }
        self.assertRaises(Exception, Central.create_experiment, data)

    def test_create_experiment_ok(self):
        pass
