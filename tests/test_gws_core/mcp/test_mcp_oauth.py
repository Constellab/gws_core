import asyncio
import base64
import hashlib
import secrets
from contextlib import asynccontextmanager
from unittest import TestCase

from fastapi import FastAPI
from gws_core.mcp import mcp_controller
from gws_core.mcp.mcp_server_builder import build_mcp_server
from gws_core.oauth import oauth_controller
from gws_core.oauth.oauth_provider import LabOAuthProvider
from gws_core.oauth.oauth_service import OAuthService
from gws_core.test.base_test_case import BaseTestCase
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.jwt_service import JWTService
from gws_core.user.unique_code_service import UniqueCodeService
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from pydantic import AnyHttpUrl
from starlette.testclient import TestClient

LAB_HOST = "lab.example.com"
MCP_URL = f"https://{LAB_HOST}/mcp"
CONSENT_PAGE_URL = "https://dev-lab.example.com/oauth-consent"
CLIENT_REDIRECT = "http://localhost:33418/callback"


def _consent_app() -> FastAPI:
    """Mount the consent route the way oauth_controller does at import time.

    Built here rather than reusing ``oauth_controller.oauth_auth_app``: that module
    attribute exists only when GWS_MCP_SERVER_ENABLED was set before the controller
    was imported, which would force the flag on for the whole test process. The
    route under test is the handler, not the registration, so wiring it onto a
    local app tests the same thing without that global.
    """
    app = FastAPI()
    app.get(f"/{oauth_controller.OAUTH_AUTH_ROUTE_PATH}/consent")(
        oauth_controller.oauth_consent
    )
    return app


def _pkce_pair() -> tuple[str, str]:
    """Return a (code_verifier, code_challenge) S256 PKCE pair."""
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    return verifier, challenge


def _build_provider() -> LabOAuthProvider:
    return LabOAuthProvider(
        consent_page_url=CONSENT_PAGE_URL,
        resource_url=MCP_URL,
        resource_name="MCP server",
        lab_url=f"https://{LAB_HOST}",
    )


def _build_client(provider: LabOAuthProvider) -> TestClient:
    """Build the app the way the lab mounts it: MCP at /mcp/, metadata at the root.

    The root app runs the MCP session manager, exactly as ``App.lifespan`` does:
    a mounted sub-app's own lifespan is never run, and without the manager any
    authenticated call fails with "Task group is not initialized".
    """
    auth_settings = AuthSettings(
        issuer_url=AnyHttpUrl(MCP_URL),
        resource_server_url=AnyHttpUrl(MCP_URL),
        client_registration_options=ClientRegistrationOptions(enabled=True),
    )
    server = build_mcp_server(
        auth_provider=provider,
        auth_settings=auth_settings,
        allowed_hosts=[LAB_HOST],
    )
    server.settings.streamable_http_path = "/"

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        async with server.session_manager.run():
            yield

    app = FastAPI(lifespan=lifespan)
    app.mount("/mcp/", server.streamable_http_app())
    mcp_controller._add_well_known_routes(app, auth_settings)
    return TestClient(app)


class _McpOAuthTestCase(BaseTestCase):
    """Shared setup: an app mounted the way the lab mounts it."""

    def setUp(self):
        self.provider = _build_provider()
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

    def _authorize(self, client_id: str, challenge: str, state: str = "the-state") -> str:
        """Run /authorize and return the login_state handed to the consent page."""
        response = self.client.get(
            "/mcp/authorize",
            params={
                "client_id": client_id,
                "redirect_uri": CLIENT_REDIRECT,
                "response_type": "code",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": state,
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        return response.headers["location"].split("login_state=")[1].split("&")[0]


# test_mcp_oauth
class TestMcpOAuthDiscovery(_McpOAuthTestCase):
    """The metadata a client needs before it can log in."""

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

    def test_authorization_server_metadata_is_served_at_the_rfc_8414_path(self):
        """Regression: our issuer has a path, so RFC 8414 clients ask for
        /.well-known/oauth-authorization-server/mcp. The SDK only serves the bare
        path, and the mismatch 404s the login before the browser opens."""
        response = self.client.get("/.well-known/oauth-authorization-server/mcp")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["issuer"], MCP_URL)

    def test_both_metadata_paths_serve_the_same_document(self):
        with_path = self.client.get("/.well-known/oauth-authorization-server/mcp").json()
        bare = self.client.get("/.well-known/oauth-authorization-server").json()

        self.assertEqual(with_path, bare)


# test_mcp_oauth
class TestMcpTransportSecurity(_McpOAuthTestCase):
    """DNS-rebinding protection must not lock out the lab's own domain."""

    def _call_with_host(self, host: str):
        """An authenticated call: transport security sits behind the auth
        middleware, so an anonymous request is 401'd before the Host is read."""
        user = CurrentUserService.get_and_check_current_user()
        token = JWTService.create_jwt(user.id)[len(JWTService.AUTH_SCHEME) :]

        return self.client.post(
            "/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Host": host,
                "Authorization": f"Bearer {token}",
                "Accept": "application/json, text/event-stream",
            },
        )

    def test_a_request_to_the_labs_own_host_is_accepted(self):
        """Regression: the SDK defaults to rebinding protection with an EMPTY
        allowed_hosts, so every non-localhost Host got 421 "Invalid Host header"
        -- the client authenticated fine, then could not connect at all."""
        self.assertNotEqual(self._call_with_host(LAB_HOST).status_code, 421)

    def test_a_request_to_an_unknown_host_is_refused(self):
        """The protection is configured, not disabled: other hosts stay rejected."""
        self.assertEqual(self._call_with_host("evil.example.com").status_code, 421)

    def test_the_host_may_carry_a_port(self):
        self.assertNotEqual(self._call_with_host(f"{LAB_HOST}:3000").status_code, 421)


# test_mcp_oauth
class TestAllowedHosts(TestCase):
    """Which Host headers the lab declares to the SDK."""

    def test_the_host_is_taken_from_the_lab_url(self):
        self.assertEqual(
            mcp_controller._get_allowed_hosts("https://glab-dev.rio.gencovery.io/mcp"),
            ["glab-dev.rio.gencovery.io"],
        )

    def test_a_port_in_the_lab_url_is_kept(self):
        self.assertEqual(
            mcp_controller._get_allowed_hosts("http://localhost:3000/mcp"),
            ["localhost:3000"],
        )


# test_mcp_oauth
class TestAuthorizationServerMetadataPaths(TestCase):
    """Which well-known paths the metadata is published on (RFC 8414 §3.1)."""

    def test_an_issuer_with_a_path_publishes_both_paths(self):
        paths = mcp_controller._authorization_server_metadata_paths(
            AnyHttpUrl("https://lab.example.com/mcp")
        )

        self.assertEqual(
            paths,
            [
                "/.well-known/oauth-authorization-server/mcp",
                "/.well-known/oauth-authorization-server",
            ],
        )

    def test_an_issuer_without_a_path_publishes_only_the_bare_path(self):
        for issuer in ["https://lab.example.com", "https://lab.example.com/"]:
            paths = mcp_controller._authorization_server_metadata_paths(AnyHttpUrl(issuer))
            self.assertEqual(paths, ["/.well-known/oauth-authorization-server"])


# test_mcp_oauth
class TestMcpClientRegistration(_McpOAuthTestCase):
    """Dynamic client registration and its persistence."""

    def test_client_can_register_itself(self):
        self.assertIsNotNone(self._register_client())

    def test_a_registered_client_survives_a_restart(self):
        """Regression: clients used to live in memory, so a lab restart made Claude's
        cached client_id permanently unknown ("Client ID '...' not found" on
        /authorize) with no way for the client to recover."""
        client_id = self._register_client()

        # A brand-new provider stands in for the process after a restart.
        client = asyncio.run(_build_provider().get_client(client_id))

        assert client is not None
        self.assertEqual(client.client_id, client_id)
        assert client.redirect_uris is not None
        self.assertEqual([str(uri) for uri in client.redirect_uris], [CLIENT_REDIRECT])

    def test_an_unknown_client_is_not_found(self):
        self.assertIsNone(asyncio.run(self.provider.get_client("no-such-client")))


# test_mcp_oauth
class TestMcpAuthorize(_McpOAuthTestCase):
    """/authorize hands the browser to the lab's own consent page."""

    def test_authorize_redirects_to_the_lab_consent_page(self):
        """The user must stay on the lab's domains: no Space, no Community."""
        client_id = self._register_client()
        _, challenge = _pkce_pair()

        response = self.client.get(
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

        self.assertEqual(response.status_code, 302)
        location = response.headers["location"]
        self.assertTrue(location.startswith(CONSENT_PAGE_URL))
        self.assertIn("login_state=", location)

    def test_authorize_passes_only_the_login_state_to_the_front_end(self):
        """The consent page needs nothing else; PKCE/redirect_uri stay server-side."""
        client_id = self._register_client()
        _, challenge = _pkce_pair()

        location = self.client.get(
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
        ).headers["location"]

        self.assertNotIn("code_challenge", location)
        self.assertNotIn("redirect_uri", location)


# test_mcp_oauth
class TestMcpConsent(_McpOAuthTestCase):
    """The consent route: the one-time code is the proof of identity."""

    def _consent_code(self) -> str:
        """Mint a code the way /core-api/user/oauth-consent-code does."""
        user = CurrentUserService.get_and_check_current_user()
        return UniqueCodeService.generate_code(user.id, {}, 60)

    def _consent(self, login_state: str, code: str):
        with TestClient(_consent_app()) as client:
            return client.get(
                "/oauth-auth/consent",
                params={"login_state": login_state, "code": code},
                follow_redirects=False,
            )

    def test_consent_redirects_back_to_the_client_with_a_code(self):
        OAuthService.set_provider(self.provider)
        self.addCleanup(OAuthService.clear)

        client_id = self._register_client()
        _, challenge = _pkce_pair()
        login_state = self._authorize(client_id, challenge)

        response = self._consent(login_state, self._consent_code())

        self.assertEqual(response.status_code, 302)
        location = response.headers["location"]
        self.assertTrue(location.startswith(CLIENT_REDIRECT))
        self.assertIn("code=", location)
        self.assertIn("state=the-state", location)

    def test_a_reused_consent_code_is_refused(self):
        """The code rides in a URL, so a replay must not authorize a second client."""
        OAuthService.set_provider(self.provider)
        self.addCleanup(OAuthService.clear)

        client_id = self._register_client()
        _, challenge = _pkce_pair()
        code = self._consent_code()

        first = self._consent(self._authorize(client_id, challenge), code)
        self.assertEqual(first.status_code, 302)

        # Same code, a fresh authorization: must not go through.
        second = self._consent(self._authorize(client_id, challenge), code)
        self.assertEqual(second.status_code, 400)

    def test_an_unknown_consent_code_is_refused(self):
        OAuthService.set_provider(self.provider)
        self.addCleanup(OAuthService.clear)

        client_id = self._register_client()
        _, challenge = _pkce_pair()
        login_state = self._authorize(client_id, challenge)

        response = self._consent(login_state, "not-a-real-code")

        self.assertEqual(response.status_code, 400)

    def test_missing_params_are_refused(self):
        with TestClient(_consent_app()) as client:
            for params in [{}, {"login_state": "x"}, {"code": "y"}]:
                response = client.get("/oauth-auth/consent", params=params, follow_redirects=False)
                self.assertEqual(response.status_code, 400)


# test_mcp_oauth
class TestMcpOAuthFlow(_McpOAuthTestCase):
    """The full authorization, from client registration to an authenticated call."""

    def test_full_flow_mints_a_working_lab_token(self):
        """Register -> authorize -> consent -> code -> token -> authenticated call."""
        client_id = self._register_client()
        verifier, challenge = _pkce_pair()
        user = CurrentUserService.get_and_check_current_user()

        login_state = self._authorize(client_id, challenge)

        # The user consents on the front-end; the lab mints the authorization code.
        redirect_url = self.provider.complete_authorization(login_state, user)
        self.assertTrue(redirect_url.startswith(CLIENT_REDIRECT))
        self.assertIn("state=the-state", redirect_url)

        code = redirect_url.split("code=")[1].split("&")[0]

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

        login_state = self._authorize(client_id, challenge)
        code = (
            self.provider.complete_authorization(login_state, user).split("code=")[1].split("&")[0]
        )

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

        login_state = self._authorize(client_id, challenge)
        code = (
            self.provider.complete_authorization(login_state, user).split("code=")[1].split("&")[0]
        )

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
class TestMcpTokenVerification(_McpOAuthTestCase):
    """What the resource server accepts as a credential."""

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
        """Notably a token from another issuer: it is not signed by this lab."""
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
