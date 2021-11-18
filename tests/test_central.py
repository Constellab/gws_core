# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import unittest

from gws_core import GTest, User, UserService


class TestCentral(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_create_user(self):
        GTest.print("Central")
        data = {
            "id": "1234567890",
            "email": "test@gencovery.com",
            "first_name": "",
            "last_name": "",
            "token": "test",
            "group": "user"
        }
        tf = UserService.create_user(data)
        self.assertTrue(tf)
        user = User.get_by_id("1234567890")
        self.assertEqual(user.id, "1234567890")
