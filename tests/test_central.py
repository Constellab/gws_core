
import unittest
from gws.model import User, Experiment
from gws.central import Central

class TestCentral(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        User.drop_table()
        Experiment.drop_table()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_central(self):
        data = {
            "uri": "1234567890",
            "token": 'my_token'
        }
        tf = Central.create_user(data)
        self.assertTrue(tf)
        user = User.get_by_uri("1234567890")
        self.assertEqual(user.token, "my_token")

        data = {
            "uri": "123456abcd",
            "user_uri": "1234567890", 
        }
        Central.open_experiment(data)
        self.assertTrue(tf)
        e = Experiment.get_by_uri("123456abcd")
        self.assertEqual(e.uri, "123456abcd")
