from gws_core.oauth.oauth_client import OAuthClient
from gws_core.test.base_test_case import BaseTestCase

CLIENT_INFO = {
    "client_id": "a-client",
    "redirect_uris": ["http://localhost:33418/callback"],
    "client_name": "Some client",
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none",
}


# test_oauth_client
class TestOAuthClient(BaseTestCase):
    """Registered clients must outlive the process that registered them.

    A client caches its client_id indefinitely, so if the registry did not
    survive a restart the client would present an id the lab has never seen and
    could never recover on its own.
    """

    def test_a_saved_client_can_be_found_again(self):
        OAuthClient.save_client("a-client", CLIENT_INFO)

        found = OAuthClient.find_by_client_id("a-client")

        assert found is not None
        self.assertEqual(found.client_id, "a-client")
        self.assertEqual(found.client_info["client_name"], "Some client")

    def test_an_unknown_client_is_not_found(self):
        self.assertIsNone(OAuthClient.find_by_client_id("no-such-client"))

    def test_saving_the_same_client_twice_updates_it(self):
        """Re-registration must not violate the unique constraint on client_id."""
        OAuthClient.save_client("a-client", CLIENT_INFO)
        OAuthClient.save_client("a-client", {**CLIENT_INFO, "client_name": "Renamed"})

        found = OAuthClient.find_by_client_id("a-client")

        assert found is not None
        self.assertEqual(found.client_info["client_name"], "Renamed")
        self.assertEqual(len(list(OAuthClient.select())), 1)

    def test_the_client_metadata_round_trips_verbatim(self):
        """The OAuth library owns that schema; we must not lose fields we ignore."""
        OAuthClient.save_client("a-client", CLIENT_INFO)

        found = OAuthClient.find_by_client_id("a-client")

        assert found is not None
        self.assertEqual(found.client_info, CLIENT_INFO)
