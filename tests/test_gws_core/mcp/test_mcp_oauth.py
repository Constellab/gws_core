import base64
import hashlib
import secrets
from contextlib import asynccontextmanager
from unittest.mock import patch

from fastapi import FastAPI
from gws_core.mcp import mcp_controller
from gws_core.mcp.db_mcp import build_mcp_server
from gws_core.mcp.mcp_oauth_provider import ConstellabOAuthProvider
from gws_core.test.base_test_case import BaseTestCase
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.jwt_service import JWTService
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from starlette.testclient import TestClient

MCP_URL = "https://lab.example.com/mcp"
CALLBACK_URL = "https://lab.example.com/mcp-auth/callback"
CLIENT_REDIRECT = "http://localhost:33418/callback"


def _pkce_pair() -> tuple[str, str]:
    """Return a (code_verifier, code_challenge) S256 PKCE pair."""
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    return verifier, challenge


def _build_client(provider: ConstellabOAuthProvider) -> TestClient:
    """Build the app the way the lab mounts it: MCP at /mcp/, metadata at the root.

    The root app runs the MCP session manager, exactly as ``App.lifespan`` does:
    a mounted sub-app's own lifespan is never run, and without the manager any
    authenticated call fails with "Task group is not initialized".
    """
    auth_settings = AuthSettings(
        issuer_url=MCP_URL,
        resource_server_url=MCP_URL,
        client_registration_options=ClientRegistrationOptions(enabled=True),
    )
    server = build_mcp_server(auth_provider=provider, auth_settings=auth_settings)
    server.settings.streamable_http_path = "/"

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        async with server.session_manager.run():
            yield

    app = FastAPI(lifespan=lifespan)
    app.mount("/mcp/", server.streamable_http_app())
    mcp_controller._add_well_known_routes(app, auth_settings)
    return TestClient(app)


# test_mcp_oauth
class TestMcpOAuthDiscovery(BaseTestCase):
    """The metadata a client needs before it can log in."""

    def setUp(self):
        self.provider = ConstellabOAuthProvider(
            callback_url=CALLBACK_URL, resource_url=MCP_URL
        )
        # Entering the TestClient context runs the app lifespan (and so the MCP
        # session manager); addCleanup exits it at the end of the test.
        self.client = _build_client(self.provider)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_unauthenticated_call_is_refused_and_points_at_the_metadata(self):
        """A 401 must advertise where the metadata lives, or discovery never starts."""
        response = self.client.post(
            "/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={"Accept": "application/json, text/event-stream"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("resource_metadata=", response.headers["www-authenticate"])

    def test_the_advertised_metadata_url_actually_resolves(self):
        """Regression: the SDK advertises a root URL, but its routes sit behind the mount."""
        response = self.client.post(
            "/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={"Accept": "application/json, text/event-stream"},
        )
        advertised = response.headers["www-authenticate"].split('resource_metadata="')[1].rstrip('"')
        path = advertised.replace("https://lab.example.com", "")

        metadata = self.client.get(path)

        self.assertEqual(metadata.status_code, 200)
        self.assertEqual(metadata.json()["resource"], MCP_URL)

    def test_authorization_server_metadata_advertises_pkce(self):
        metadata = self.client.get("/.well-known/oauth-authorization-server").json()

        self.assertEqual(metadata["code_challenge_methods_supported"], ["S256"])
        self.assertEqual(metadata["authorization_endpoint"], f"{MCP_URL}/authorize")
        self.assertEqual(metadata["token_endpoint"], f"{MCP_URL}/token")


# test_mcp_oauth
class TestMcpOAuthFlow(BaseTestCase):
    """The full browser login, from client registration to an authenticated call."""

    def setUp(self):
        self.provider = ConstellabOAuthProvider(
            callback_url=CALLBACK_URL, resource_url=MCP_URL
        )
        # Entering the TestClient context runs the app lifespan (and so the MCP
        # session manager); addCleanup exits it at the end of the test.
        self.client = _build_client(self.provider)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def _register_client(self) -> str:
        response = self.client.post(
            "/mcp/register",
            json={
                "redirect_uris": [CLIENT_REDIRECT],
                "client_name": "Claude Code",
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["client_id"]

    def test_client_can_register_itself(self):
        self.assertIsNotNone(self._register_client())

    def test_full_flow_mints_a_working_lab_token(self):
        """Register -> authorize -> Constellab login -> code -> token -> authenticated call."""
        client_id = self._register_client()
        verifier, challenge = _pkce_pair()
        user = CurrentUserService.get_and_check_current_user()

        # /authorize hands the browser off to Constellab
        with patch(
            "gws_core.mcp.mcp_constellab_login.ConstellabLoginService.request_device_code",
            return_value=("device-code", "https://constellab.community/cli-auth?code=x"),
        ):
            authorize = self.client.get(
                "/mcp/authorize",
                params={
                    "client_id": client_id,
                    "redirect_uri": CLIENT_REDIRECT,
                    "response_type": "code",
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "state": "the-state",
                },
                follow_redirects=False,
            )
        self.assertEqual(authorize.status_code, 302)

        # The user comes back from Constellab; the lab resolves them and mints a code
        login_state = authorize.headers["location"].split("login_state=")[1].split("&")[0]
        redirect_url = self.provider.complete_authorization(login_state, user)
        self.assertTrue(redirect_url.startswith(CLIENT_REDIRECT))
        self.assertIn("state=the-state", redirect_url)

        code = redirect_url.split("code=")[1].split("&")[0]

        # The code is exchanged for a lab JWT
        token_response = self.client.post(
            "/mcp/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "redirect_uri": CLIENT_REDIRECT,
                "code_verifier": verifier,
            },
        )
        self.assertEqual(token_response.status_code, 200)
        access_token = token_response.json()["access_token"]

        # The minted token is a real lab JWT for this user
        self.assertEqual(
            JWTService.check_user_access_token(JWTService.AUTH_SCHEME + access_token),
            user.id,
        )

        # And it authenticates an actual MCP call
        call = self.client.post(
            "/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json, text/event-stream",
            },
        )
        self.assertNotEqual(call.status_code, 401)

    def test_authorization_code_is_single_use(self):
        """A replayed code must not yield a second token."""
        client_id = self._register_client()
        verifier, challenge = _pkce_pair()
        user = CurrentUserService.get_and_check_current_user()

        with patch(
            "gws_core.mcp.mcp_constellab_login.ConstellabLoginService.request_device_code",
            return_value=("device-code", "https://constellab.community/cli-auth?code=x"),
        ):
            authorize = self.client.get(
                "/mcp/authorize",
                params={
                    "client_id": client_id,
                    "redirect_uri": CLIENT_REDIRECT,
                    "response_type": "code",
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "state": "s",
                },
                follow_redirects=False,
            )
        login_state = authorize.headers["location"].split("login_state=")[1].split("&")[0]
        code = self.provider.complete_authorization(login_state, user).split("code=")[1].split("&")[0]

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "redirect_uri": CLIENT_REDIRECT,
            "code_verifier": verifier,
        }
        self.assertEqual(self.client.post("/mcp/token", data=payload).status_code, 200)
        self.assertNotEqual(self.client.post("/mcp/token", data=payload).status_code, 200)

    def test_wrong_pkce_verifier_is_refused(self):
        """An intercepted code is useless without the verifier."""
        client_id = self._register_client()
        _, challenge = _pkce_pair()
        user = CurrentUserService.get_and_check_current_user()

        with patch(
            "gws_core.mcp.mcp_constellab_login.ConstellabLoginService.request_device_code",
            return_value=("device-code", "https://constellab.community/cli-auth?code=x"),
        ):
            authorize = self.client.get(
                "/mcp/authorize",
                params={
                    "client_id": client_id,
                    "redirect_uri": CLIENT_REDIRECT,
                    "response_type": "code",
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "state": "s",
                },
                follow_redirects=False,
            )
        login_state = authorize.headers["location"].split("login_state=")[1].split("&")[0]
        code = self.provider.complete_authorization(login_state, user).split("code=")[1].split("&")[0]

        response = self.client.post(
            "/mcp/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "redirect_uri": CLIENT_REDIRECT,
                "code_verifier": "not-the-right-verifier",
            },
        )

        self.assertEqual(response.status_code, 400)


# test_mcp_oauth
class TestMcpTokenVerification(BaseTestCase):
    """What the resource server accepts as a credential."""

    def setUp(self):
        self.provider = ConstellabOAuthProvider(
            callback_url=CALLBACK_URL, resource_url=MCP_URL
        )
        # Entering the TestClient context runs the app lifespan (and so the MCP
        # session manager); addCleanup exits it at the end of the test.
        self.client = _build_client(self.provider)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_a_valid_lab_jwt_is_accepted(self):
        user = CurrentUserService.get_and_check_current_user()
        token = JWTService.create_jwt(user.id)[len(JWTService.AUTH_SCHEME) :]

        response = self.client.post(
            "/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json, text/event-stream",
            },
        )

        self.assertNotEqual(response.status_code, 401)

    def test_garbage_and_foreign_tokens_are_refused(self):
        """Notably a community token: it is signed by another issuer, not the lab."""
        foreign = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiIxIiwiZXhwIjo5OTk5OTk5OTk5fQ"
            ".this-signature-is-not-from-this-lab"
        )

        for token in ["not-a-jwt", foreign, ""]:
            response = self.client.post(
                "/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json, text/event-stream",
                },
            )
            self.assertEqual(response.status_code, 401)
