from gws_core import BaseTestCase
from gws_core.apps.apps_manager import AppsManager
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.jwt_service import JWTService
from gws_core.user.unique_code_service import (
    InvalidUniqueCodeException,
    UniqueCodeService,
)


class TestAppGatewayAuth(BaseTestCase):
    """Tests for the app launcher auth pieces: the code -> JWT exchange and the
    single-use code semantics that back both the app handoff and the space link.
    """

    def test_exchange_app_code_happy_path(self):
        """A code minted for an app exchanges into a JWT that resolves to the same user."""
        user = CurrentUserService.get_and_check_current_user()
        app_id = "app-1"

        code = AppsManager.generate_app_access_code(user.id, app_id)
        result = AppsManager.exchange_app_code(app_id, code)

        self.assertEqual(result.user_id, user.id)
        # the returned user_access_token is a real JWT resolving to the user
        self.assertEqual(JWTService.check_user_access_token(result.user_access_token), user.id)

    def test_exchange_app_code_is_single_use(self):
        """The code is consumed on first exchange; a second exchange is rejected."""
        user = CurrentUserService.get_and_check_current_user()
        app_id = "app-1"

        code = AppsManager.generate_app_access_code(user.id, app_id)
        AppsManager.exchange_app_code(app_id, code)

        with self.assertRaises(InvalidUniqueCodeException):
            AppsManager.exchange_app_code(app_id, code)

    def test_exchange_app_code_wrong_app_rejected(self):
        """A code minted for one app cannot be exchanged against another app."""
        user = CurrentUserService.get_and_check_current_user()

        code = AppsManager.generate_app_access_code(user.id, "app-1")

        with self.assertRaises(InvalidUniqueCodeException):
            AppsManager.exchange_app_code("app-2", code)

    def test_space_access_code_round_trip(self):
        """The space link code carries the share link id and resolves the user once."""
        user = CurrentUserService.get_and_check_current_user()
        share_link_id = "share-1"

        code = UniqueCodeService.generate_code(
            user.id, {"share_link_id": share_link_id}, 60
        )

        code_obj = UniqueCodeService.check_code(code)
        self.assertEqual(code_obj.user_id, user.id)
        self.assertEqual(code_obj.obj.get("share_link_id"), share_link_id)

        # single-use: a second check is rejected
        with self.assertRaises(InvalidUniqueCodeException):
            UniqueCodeService.check_code(code)
