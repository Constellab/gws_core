# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BaseTestCase, UserService
from gws_core.lab.dev_env_service import DevEnvService
from gws_core.user.auth_service import AuthService
from gws_core.user.user import UserDataDict


# test_dev_env_service
class TestDevEnvService(BaseTestCase):

    def test_dev_login(self):

        # create the user
        user_data: UserDataDict = {
            "id": "06866542-f089-46dc-b57f-a11e25a23aa5",
            "email": "test_mail@gencovery.com",
            "first_name": "Firstname test",
            "last_name": "Lastname test",
            "group": "ADMIN",
            "is_active": True,
            "theme": "light-theme",
            "lang": "en",
            "photo": None
        }

        user = UserService.create_or_update_user(user_data)

        # Generate the unique code
        unique_code = DevEnvService.generate_dev_login_unique_code(user.id)

        # Simulate call from dev to prod API to check the unique code
        user_data_db = DevEnvService.check_dev_login_unique_code(unique_code)

        # check that the user is the same
        self.assert_json(user_data, user_data_db.to_user_data_dict())

        # check that we can generate the response containing token
        response = AuthService.log_user(user_data_db)

        self.assertEqual(response.status_code, 200)
