import os
import unittest
import json

from gws.model import User, Experiment, Protocol
from gws.central import Central
from gws.settings import Settings

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

    def test_create_experiment_execption(self):
        data = {
            "uri": "123456abcd",
            "protocol": {
                "uri": "1234ERTY",
            }
        }
        self.assertRaises(Exception, Central.create_experiment, data)

    def test_create_experiment_ok(self):
        import tests.test_protocol 
        settings = Settings.retrieve()
        testdata_dir = settings.get_dir("gws:testdata_dir")

        with open(os.path.join(testdata_dir, "protocol_graph.json"), "r") as f:
            graph = json.load(f)

        # test execption
        data = {
            "uri": "123456abcd",
            "protocol": {
                "uri": "1234ERTY",
                "graph": graph
            }
        }
        tf = Central.create_experiment(data)
        self.assertTrue(tf)
        e = Experiment.get_by_uri("123456abcd")
        self.assertEqual(e.uri, "123456abcd")

        proto = Protocol.get_by_id(e.protocol.id)
        self.assertEqual(proto.dumps(as_dict=True), graph)
