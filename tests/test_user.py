# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json

from gws_core import User, UserGroup, UserService
from gws_core.user.auth_service import AuthService
from gws_core.user.jwt_service import JWTService
from gws_core.user.user_dto import UserData, UserDataDict
from starlette.responses import JSONResponse

from tests.base_test import BaseTest


class TestUser(BaseTest):

    async def test_sysuser_and_owner(self):
        """
        Simple test to check that the sysuser and owner users are created
        """
        user: User = UserService.get_sysuser()
        self.assertIsNotNone(user.id)

    async def test_user_create(self):
        """
        Test the user creation from a json
        """

        user_data: UserDataDict = {
            "uri": "06866542-f089-46dc-b57f-a11e25a23aa5",
            "email": "test_mail@gencovery.com",
            "first_name": "Firstname test",
            "last_name": "Lastname test",
            "group": "ADMIN",
            "is_active": True,
            "is_admin": True
        }
        UserService.create_user(user_data)

        user_db: User = UserService.get_user_by_uri("06866542-f089-46dc-b57f-a11e25a23aa5")

        self.assertEqual(user_db.email, 'test_mail@gencovery.com')
        self.assertEqual(user_db.first_name, 'Firstname test')
        self.assertEqual(user_db.last_name, 'Lastname test')
        self.assertEqual(user_db.group, UserGroup.ADMIN)

    async def test_authentication(self):
        """
        Test that a user can authenticate
        """
        user_data: UserDataDict = {
            "uri": "06866542-f089-46dc-b57f-a11e25a23aa6",
            "email": "test_mail@gencovery.com",
            "first_name": "Firstname test",
            "last_name": "Lastname test",
            "group": "ADMIN",
            "is_active": True,
            "is_admin": True
        }
        UserService.create_user(user_data)

        json_repsonse: JSONResponse = AuthService.generate_user_access_token("06866542-f089-46dc-b57f-a11e25a23aa6")
        # extract the json form the repsonse Byte literal
        token: str = json.loads(json_repsonse.body.decode('utf8').replace("'", '"'))["access_token"]

        user_uri: str = JWTService.check_user_access_token(token)

        self.assertEqual(user_uri, "06866542-f089-46dc-b57f-a11e25a23aa6")