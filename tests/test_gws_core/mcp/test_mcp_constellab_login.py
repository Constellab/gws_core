import base64
import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

from gws_core.mcp.mcp_constellab_login import (
    ConstellabLoginError,
    ConstellabLoginService,
)


def _response(status_code: int, json_body: dict | None = None) -> MagicMock:
    """Build a fake requests.Response for the community endpoint."""
    response = MagicMock()
    response.status_code = status_code
    if json_body is None:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = json_body
    return response


# test_mcp_constellab_login
class TestConstellabLoginPolling(TestCase):
    """poll_for_token: pending vs. done vs. refused."""

    def _poll(self, response: MagicMock) -> str | None:
        with patch(
            "gws_core.mcp.mcp_constellab_login.ExternalApiService.post",
            return_value=response,
        ):
            return ConstellabLoginService.poll_for_token("device-code")

    def test_returns_the_token_once_the_user_has_logged_in(self):
        self.assertEqual(self._poll(_response(200, {"token": "the-token"})), "the-token")

    def test_accepts_the_camel_case_and_snake_case_token_fields(self):
        self.assertEqual(self._poll(_response(200, {"accessToken": "t"})), "t")
        self.assertEqual(self._poll(_response(200, {"access_token": "t"})), "t")

    def test_returns_none_while_the_login_is_still_pending(self):
        """A pending poll must not raise: the caller polls again."""
        self.assertIsNone(self._poll(_response(202, {"status": "pending"})))

    def test_returns_none_when_the_response_has_no_token(self):
        self.assertIsNone(self._poll(_response(200, {})))

    def test_returns_none_on_a_non_json_response(self):
        self.assertIsNone(self._poll(_response(200, None)))

    def test_returns_none_on_a_network_error(self):
        with patch(
            "gws_core.mcp.mcp_constellab_login.ExternalApiService.post",
            side_effect=OSError("boom"),
        ):
            self.assertIsNone(ConstellabLoginService.poll_for_token("device-code"))

    def test_raises_when_the_code_expired(self):
        for response in [_response(410, {}), _response(200, {"status": "expired"})]:
            with self.assertRaises(ConstellabLoginError):
                self._poll(response)

    def test_raises_when_the_login_was_denied(self):
        for response in [_response(409, {}), _response(200, {"status": "denied"})]:
            with self.assertRaises(ConstellabLoginError):
                self._poll(response)


# test_mcp_constellab_login
class TestConstellabIdentity(TestCase):
    """get_email_from_token: the identity the lab maps to a user."""

    @staticmethod
    def _jwt_with(payload_b64: str) -> str:
        return f"header.{payload_b64}.signature"

    def test_reads_the_email_from_the_token(self):
        payload = base64.urlsafe_b64encode(
            json.dumps({"email": "someone@gencovery.com"}).encode()
        ).decode().rstrip("=")

        email = ConstellabLoginService.get_email_from_token(self._jwt_with(payload))

        self.assertEqual(email, "someone@gencovery.com")

    def test_raises_when_the_token_carries_no_email(self):
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "1"}).encode()).decode().rstrip("=")

        with self.assertRaises(ConstellabLoginError):
            ConstellabLoginService.get_email_from_token(self._jwt_with(payload))

    def test_raises_on_a_malformed_token(self):
        for token in ["not-a-jwt", "", "a.b"]:
            with self.assertRaises(ConstellabLoginError):
                ConstellabLoginService.get_email_from_token(token)
