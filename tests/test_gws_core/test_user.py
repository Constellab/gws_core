

from gws_core import BaseTestCase, User, UserGroup, UserService
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.user.auth_service import AuthService
from gws_core.user.user_dto import UserFullDTO, UserTheme


# test_user
class TestUser(BaseTestCase):

    def test_sysuser(self):
        """
        Simple test to check that the sysuser is created
        """
        user: User = UserService.get_sysuser()
        self.assertTrue(user.is_saved())

    def test_user_create(self):
        """
        Test the user creation from a json
        """
        user_dto = UserFullDTO(
            id="06866542-f089-46dc-b57f-a11e25a23aa5",
            email="test_mail@gencovery.com",
            first_name="Firstname test",
            last_name="Lastname test",
            group=UserGroup.USER,
            is_active=True,
            theme=UserTheme.LIGHT_THEME,
        )
        UserService.create_or_update_user_dto(user_dto)

        user_db: User = UserService.get_user_by_id("06866542-f089-46dc-b57f-a11e25a23aa5")

        self.assertEqual(user_db.email, 'test_mail@gencovery.com')
        self.assertEqual(user_db.first_name, 'Firstname test')
        self.assertEqual(user_db.last_name, 'Lastname test')
        self.assertEqual(user_db.group, UserGroup.USER)

    def test_authentication(self):
        """
        Test that a user can authenticate
        """
        user_dto = UserFullDTO(
            id="06866542-f089-46dc-b57f-a11e25a23aa5",
            email="test_mail@gencovery.com",
            first_name="Firstname test",
            last_name="Lastname test",
            group=UserGroup.USER,
            is_active=True,
            theme=UserTheme.LIGHT_THEME,
        )
        UserService.create_or_update_user_dto(user_dto)

        token = AuthService.generate_user_access_token(user_dto.id)

        user_data: User = AuthService.check_user_access_token(token)
        self.assertEqual(user_data.id, user_dto.id)

    def test_deactivate_user(self):
        self._delete_users()

        user: User = User()
        user.email = "testpol@gencovery.com"
        user.first_name = "Michel"
        user.last_name = "Pol"
        user.group = UserGroup.ADMIN
        user.save()

        user2: User = User()
        user2.email = "testbeau@gencovery.com"
        user2.first_name = "Jack"
        user2.last_name = "Beauregard"
        user2.group = UserGroup.ADMIN
        user2.save()

        user3: User = User()
        user3.email = "fred@gencovery.com"
        user3.first_name = "Freddy"
        user3.last_name = "Mercury"
        user3.group = UserGroup.USER
        user3.save()

        UserService.deactivate_user(user.id)
        UserService.deactivate_user(user3.id)

        # can't deactivate the last admin
        self.assertRaises(BadRequestException, UserService.deactivate_user, user2.id)

    def test_user_search(self):
        """
        Test the user search
        """
        self._delete_users()
        user: User = User()
        user.email = "test@gencovery.com"
        user.first_name = "Michel"
        user.last_name = "Dupont"
        user.group = UserGroup.USER
        user.save()

        user2: User = User()
        user2.email = "test2@gencovery.com"
        user2.first_name = "Jacques"
        user2.last_name = "Brel"
        user2.group = UserGroup.USER
        user2.save()

        # Firstname or lastname
        users = list(User.search_by_firstname_or_lastname("che"))
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].id, user.id)

        users = list(User.search_by_firstname_or_lastname("pon"))
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].id, user.id)

        # Firstname and lastname
        users = list(User.search_by_firstname_and_lastname("mich", "Dupo"))
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].id, user.id)

        users = list(User.search_by_firstname_and_lastname("dup", "mich"))
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].id, user.id)

        # test smart search
        users_page = UserService.smart_search_by_name("mich dup")
        self.assertEqual(users_page.page_info.total_number_of_items, 1)
        self.assertEqual(users_page.results[0].id, user.id)

        users_page = UserService.smart_search_by_name("dup mich")
        self.assertEqual(users_page.page_info.total_number_of_items, 1)
        self.assertEqual(users_page.results[0].id, user.id)

        users_page = UserService.smart_search_by_name("mich")
        self.assertEqual(users_page.page_info.total_number_of_items, 1)
        self.assertEqual(users_page.results[0].id, user.id)

    def _delete_users(self):
        User.delete().where(User.group != UserGroup.SYSUSER).execute()
