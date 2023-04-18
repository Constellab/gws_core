# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BaseTestCase, User, UserGroup, UserService
from gws_core.user.auth_service import AuthService
from gws_core.user.user import UserDataDict


# test_user
class TestUser(BaseTestCase):

    def test_sysuser_and_owner(self):
        """
        Simple test to check that the sysuser and owner users are created
        """
        user: User = UserService.get_sysuser()
        self.assertTrue(user.is_saved())

    def test_user_create(self):
        """
        Test the user creation from a json
        """

        user_data: UserDataDict = {
            "id": "06866542-f089-46dc-b57f-a11e25a23aa5",
            "email": "test_mail@gencovery.com",
            "first_name": "Firstname test",
            "last_name": "Lastname test",
            "group": "ADMIN",
            "is_active": True,
            "theme": "light-theme",
            "lang": "en"
        }
        UserService.create_or_update_user(user_data)

        user_db: User = UserService.get_user_by_id("06866542-f089-46dc-b57f-a11e25a23aa5")

        self.assertEqual(user_db.email, 'test_mail@gencovery.com')
        self.assertEqual(user_db.first_name, 'Firstname test')
        self.assertEqual(user_db.last_name, 'Lastname test')
        self.assertEqual(user_db.group, UserGroup.ADMIN)

    def test_authentication(self):
        """
        Test that a user can authenticate
        """
        user_data: UserDataDict = {
            "id": "06866542-f089-46dc-b57f-a11e25a23aa6",
            "email": "test_mail@gencovery.com",
            "first_name": "Firstname test",
            "last_name": "Lastname test",
            "group": "ADMIN",
            "is_active": True,
            "theme": "light-theme",
            "lang": "en"
        }
        UserService.create_or_update_user(user_data)

        token = AuthService.generate_user_access_token("06866542-f089-46dc-b57f-a11e25a23aa6")

        user_data: User = AuthService.check_user_access_token(token)
        self.assertEqual(user_data.id, "06866542-f089-46dc-b57f-a11e25a23aa6")
