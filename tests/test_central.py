import unittest

from gws.model import Experiment, Protocol, User
from gws.service.user_service import UserService


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
            "uri": "1234567890",
            "email": "test@gencovery.com",
            "first_name": "",
            "last_name": "",
            "token": "test",
            "group": "user"
        }
        tf = UserService.create_user(data)
        self.assertTrue(tf)
        user = User.get_by_uri("1234567890")
        self.assertEqual(user.uri, "1234567890")
