from gws_core import BaseTestCase
from gws_core.apps.apps_manager import AppsManager
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.jwt_service import JWTService
from gws_core.user.unique_code_service import (
    InvalidUniqueCodeException,
    UniqueCodeService,
)
from gws_core.user.user_exception import InvalidTokenException


class TestAppGatewayAuth(BaseTestCase):
    """Tests for the app launcher auth pieces: the code -> JWT exchange and the
    single-use code semantics that back both the app handoff and the space link.
    """

    def test_exchange_app_code_happy_path(self):
        """A code minted for an app exchanges into an app-scoped token for the same user."""
        user = CurrentUserService.get_and_check_current_user()
        app_id = "app-1"

        code = AppsManager.generate_app_access_code(user.id, app_id)
        result = AppsManager.exchange_app_code(app_id, code)

        self.assertEqual(result.user_id, user.id)
        # the returned token is an APP-scoped token: it resolves to the user only when checked as
        # an app token for this app...
        self.assertEqual(
            JWTService.check_app_access_token(result.user_access_token, app_id), user.id
        )
        # ...and is REJECTED when presented as a general user session token (the scope boundary).
        with self.assertRaises(InvalidTokenException):
            JWTService.check_user_access_token(result.user_access_token)

    def test_app_token_rejected_for_other_app(self):
        """An app-scoped token minted for one app cannot authenticate against another app."""
        user = CurrentUserService.get_and_check_current_user()
        code = AppsManager.generate_app_access_code(user.id, "app-1")
        exchanged = AppsManager.exchange_app_code("app-1", code)

        # validate_app_jwt binds to the app_id; a different app_id is rejected
        with self.assertRaises(InvalidTokenException):
            AppsManager.validate_app_jwt("app-2", exchanged.user_access_token)

    def test_general_session_jwt_is_not_an_app_token(self):
        """A general user-session JWT must not pass app-token validation."""
        user = CurrentUserService.get_and_check_current_user()
        session_jwt = JWTService.create_jwt(user.id)

        # general session JWT authenticates a user route...
        self.assertEqual(JWTService.check_user_access_token(session_jwt), user.id)
        # ...but is NOT a valid app token (no typ:app / app_id claim)
        with self.assertRaises(InvalidTokenException):
            JWTService.check_app_access_token(session_jwt, "app-1")

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

    def test_validate_app_jwt_round_trip(self):
        """A JWT obtained from an exchange validates back to the same user (cookie-refresh path)."""
        user = CurrentUserService.get_and_check_current_user()
        app_id = "app-1"

        code = AppsManager.generate_app_access_code(user.id, app_id)
        exchanged = AppsManager.exchange_app_code(app_id, code)

        # the JWT (as stored in the gws_app_jwt cookie) re-validates on a fresh load
        result = AppsManager.validate_app_jwt(app_id, exchanged.user_access_token)
        self.assertEqual(result.user_id, user.id)

    def test_validate_app_jwt_accepts_bare_token(self):
        """validate_app_jwt tolerates a JWT with or without the 'Bearer ' prefix."""
        user = CurrentUserService.get_and_check_current_user()
        code = AppsManager.generate_app_access_code(user.id, "app-1")
        exchanged = AppsManager.exchange_app_code("app-1", code)

        bare = exchanged.user_access_token.removeprefix("Bearer ")
        result = AppsManager.validate_app_jwt("app-1", bare)
        self.assertEqual(result.user_id, user.id)

    def test_validate_app_jwt_rejects_garbage(self):
        """An invalid JWT is rejected."""
        with self.assertRaises(InvalidTokenException):
            AppsManager.validate_app_jwt("app-1", "not-a-jwt")

    def test_validate_app_jwt_does_not_renew_a_fresh_token(self):
        """A just-minted token is not re-minted: most validations must stay read-only."""
        user = CurrentUserService.get_and_check_current_user()
        code = AppsManager.generate_app_access_code(user.id, "app-1")
        exchanged = AppsManager.exchange_app_code("app-1", code)

        result = AppsManager.validate_app_jwt("app-1", exchanged.user_access_token)
        self.assertIsNone(result.renewed_jwt)

    def test_validate_app_jwt_renews_a_half_expired_token(self):
        """A more-than-half-expired token is re-minted, giving the app a *sliding* session.

        Without this the token dies a fixed 2 days after the handoff and the user is bounced
        mid-session even while actively using the app.
        """
        user = CurrentUserService.get_and_check_current_user()
        app_id = "app-1"

        # mint a token that is already past halfway by shortening the configured lifetime
        original_duration = JWTService.ACCESS_TOKEN_EXPIRE_SECONDS
        try:
            JWTService.ACCESS_TOKEN_EXPIRE_SECONDS = 10
            old_token = JWTService.create_app_jwt(user.id, app_id)
        finally:
            JWTService.ACCESS_TOKEN_EXPIRE_SECONDS = original_duration

        # against the real (much longer) lifetime, 10s of remaining validity is past halfway
        result = AppsManager.validate_app_jwt(app_id, old_token)

        self.assertEqual(result.user_id, user.id)
        self.assertIsNotNone(result.renewed_jwt)
        # the replacement is a usable app token for the same user and app
        self.assertEqual(JWTService.check_app_access_token(result.renewed_jwt, app_id), user.id)

    def test_app_token_needs_refresh_ignores_undecodable_tokens(self):
        """Garbage never reports as needing a refresh; the caller's validation reports it instead."""
        self.assertFalse(JWTService.app_token_needs_refresh("not-a-jwt"))

    def test_authorize_grant_round_trip(self):
        """The authorize grant (start->handoff carrier) resolves the user once, is single-use."""
        user = CurrentUserService.get_and_check_current_user()
        app_id = "app-1"

        grant = AppsManager.generate_authorize_grant(user.id, app_id)
        self.assertEqual(AppsManager.consume_authorize_grant(app_id, grant), user.id)

        # single-use: a second consume is rejected
        with self.assertRaises(InvalidUniqueCodeException):
            AppsManager.consume_authorize_grant(app_id, grant)

    def test_authorize_grant_wrong_app_rejected(self):
        """An authorize grant minted for one app cannot be consumed for another app."""
        user = CurrentUserService.get_and_check_current_user()
        grant = AppsManager.generate_authorize_grant(user.id, "app-1")

        with self.assertRaises(InvalidUniqueCodeException):
            AppsManager.consume_authorize_grant("app-2", grant)

    def test_authorize_grant_is_not_an_app_grant(self):
        """An authorize grant is bound under a distinct key and is not a valid app access code."""
        user = CurrentUserService.get_and_check_current_user()
        grant = AppsManager.generate_authorize_grant(user.id, "app-1")

        # the authorize grant must NOT be exchangeable as an app code (different payload key)
        with self.assertRaises(InvalidUniqueCodeException):
            AppsManager.exchange_app_code("app-1", grant)

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
