

from gws_core import BaseTestCase, UserService
from gws_core.lab.dev_env_service import DevEnvService
from gws_core.user.authentication_service import AuthenticationService
from gws_core.user.user_dto import UserFullDTO, UserLanguage, UserTheme
from gws_core.user.user_group import UserGroup


# test_dev_env_service
class TestDevEnvService(BaseTestCase):

    def test_dev_login(self):

        user_dto = UserFullDTO(
            id="06866542-f089-46dc-b57f-a11e25a23aa5",
            email="test_mail@gencovery.com",
            first_name="Firstname test",
            last_name="Lastname test",
            group=UserGroup.ADMIN,
            is_active=True,
            theme=UserTheme.LIGHT_THEME,
            lang=UserLanguage.EN,
            photo=None
        )

        user = UserService.create_or_update_user_dto(user_dto)

        # Generate the unique code
        unique_code = DevEnvService.generate_dev_login_unique_code(user.id)

        # Simulate call from dev to prod API to check the unique code
        user_data_db = DevEnvService.check_dev_login_unique_code(unique_code)

        # check that the user is the same
        self.assertEqual(user_dto.to_json_str(), user_data_db.to_full_dto().to_json_str())

        # check that we can generate the response containing token
        response = AuthenticationService.log_user(user_data_db)

        self.assertEqual(response.status_code, 200)
