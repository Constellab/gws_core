# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import User, UserService
from gws_core.test.base_test_case import BaseTestCase


class TestSpace(BaseTestCase):

    def test_create_user(self):
        data = {
            "id": "1234567890",
            "email": "test@gencovery.com",
            "first_name": "",
            "last_name": "",
            "group": "user"
        }
        tf = UserService.create_user_if_not_exists(data)
        self.assertTrue(tf)
        user = User.get_by_id("1234567890")
        self.assertEqual(user.id, "1234567890")
