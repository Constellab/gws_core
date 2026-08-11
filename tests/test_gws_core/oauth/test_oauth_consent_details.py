import asyncio

import gws_core.oauth.oauth_provider as provider_module
from gws_core.oauth.oauth_client import OAuthClient
from gws_core.oauth.oauth_provider import LabOAuthProvider
from gws_core.test.base_test_case import BaseTestCase
from gws_core.user.current_user_service import CurrentUserService
from mcp.server.auth.provider import AuthorizationParams
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyUrl

LAB_URL = "https://lab.example.com"
RESOURCE_URL = f"{LAB_URL}/mcp"
CLIENT_REDIRECT = "http://localhost:33418/callback"


def _build_provider() -> LabOAuthProvider:
    return LabOAuthProvider(
        consent_page_url=f"{LAB_URL}/oauth-consent",
        resource_url=RESOURCE_URL,
        resource_name="MCP server",
        lab_url=LAB_URL,
    )


def _client_info(client_name: str = "Claude Code") -> OAuthClientInformationFull:
    return OAuthClientInformationFull(
        client_id="a-client",
        client_name=client_name,
        redirect_uris=[AnyUrl(CLIENT_REDIRECT)],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        token_endpoint_auth_method="none",
    )


def _authorization_params(scopes: list[str] | None = None) -> AuthorizationParams:
    return AuthorizationParams(
        state="a-state",
        scopes=scopes,
        code_challenge="a-challenge",
        redirect_uri=AnyUrl(CLIENT_REDIRECT),
        redirect_uri_provided_explicitly=True,
    )


# test_oauth_consent_details
class TestOAuthConsentDetails(BaseTestCase):
    """What the consent page is told it is asking the user to approve."""

    def setUp(self):
        self.provider = _build_provider()
        self.user = CurrentUserService.get_and_check_current_user()

    def _open_authorization(self, client_name: str = "Claude Code") -> str:
        """Register a client and start an authorization; return its login_state."""
        client = _client_info(client_name)
        asyncio.run(self.provider.register_client(client))
        redirect = asyncio.run(self.provider.authorize(client, _authorization_params()))
        return redirect.split("login_state=")[1].split("&")[0]

    def _details(self, login_state: str):
        return asyncio.run(self.provider.get_consent_details(login_state, self.user))

    def _existing_details(self, login_state: str):
        """Like :meth:`_details`, for the cases that require a consent screen."""
        details = self._details(login_state)
        assert details is not None
        return details

    def test_details_describe_the_client_the_lab_and_the_user(self):
        details = self._existing_details(self._open_authorization())

        self.assertEqual(details.client_name, "Claude Code")
        self.assertEqual(details.client_id, "a-client")
        self.assertEqual(details.resource_name, "MCP server")
        self.assertEqual(details.lab_url, LAB_URL)
        self.assertEqual(details.user_email, self.user.email)

    def test_the_client_name_is_never_presented_as_verified(self):
        """Registration is open: a client may call itself anything at all."""
        details = self._existing_details(
            self._open_authorization("Constellab Official Integration")
        )

        self.assertEqual(details.client_name, "Constellab Official Integration")
        self.assertFalse(details.client_name_is_verified)

    def test_details_admit_the_token_grants_full_access(self):
        """The lab issues a full session JWT, so the page must not imply less.

        This is the point of the endpoint: hardcoded front-end copy once claimed
        "read-only SQL queries", which described the tools, not the token.
        """
        details = self._existing_details(self._open_authorization())

        self.assertEqual(details.access_level, "full")
        assert details.warning is not None
        self.assertIn("same permissions as your account", details.warning)

    def test_details_are_none_for_an_unknown_request(self):
        """Nothing valid to consent to -> the page must not show a consent screen."""
        self.assertIsNone(self._details("not-a-real-login-state"))

    def test_details_are_none_once_the_authorization_is_consumed(self):
        login_state = self._open_authorization()
        self.provider.complete_authorization(login_state, self.user)

        self.assertIsNone(self._details(login_state))

    def test_details_are_none_when_the_client_is_gone(self):
        login_state = self._open_authorization()
        client = OAuthClient.find_by_client_id("a-client")
        assert client is not None
        client.delete_instance()

        self.assertIsNone(self._details(login_state))


# test_oauth_consent_details
class TestAccessDescription(BaseTestCase):
    """The wording is derived from what is really issued, not hardcoded."""

    def test_unscoped_tokens_are_described_as_full_access(self):
        described = LabOAuthProvider._describe_access(["mcp:read"])

        # Scopes are not enforced, so asking for a narrow scope grants everything.
        self.assertEqual(described["access_level"], "full")
        self.assertIsNotNone(described["warning"])

    def test_the_description_follows_scope_enforcement(self):
        """When scopes land, the page reports the narrower truth with no FE change."""
        original = provider_module.SCOPES_ARE_ENFORCED
        provider_module.SCOPES_ARE_ENFORCED = True
        self.addCleanup(setattr, provider_module, "SCOPES_ARE_ENFORCED", original)

        described = LabOAuthProvider._describe_access(["mcp:read"])

        self.assertEqual(described["access_level"], "scoped")
        self.assertEqual(described["access_details"], ["mcp:read"])
        self.assertIsNone(described["warning"])
