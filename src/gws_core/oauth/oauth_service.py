"""Access to the lab's OAuth authorization server.

The provider is a singleton built at startup (its URLs come from ``Settings``, which
is not loaded at import time). It lives here rather than next to any one transport so
that code needing it -- the consent endpoints, and any future protected resource --
depends on the OAuth package, not on the MCP one.
"""

from gws_core.core.utils.settings import Settings
from gws_core.oauth.oauth_provider import LabOAuthProvider

# Route of the consent page on the lab front-end. Must match the front-end's router
# (see docs/todo/oauth_consent_frontend_spec.md). The page is not tied to any one
# protected resource: it consents to any OAuth client.
CONSENT_PAGE_ROUTE = "oauth-consent"


class OAuthService:
    """Holds the lab's OAuth provider instance."""

    _provider: LabOAuthProvider | None = None

    @classmethod
    def get_consent_page_url(cls) -> str:
        """Absolute URL of the lab front-end page where a user approves a client.

        Implemented by the front-end (see ``docs/todo/oauth_consent_frontend_spec.md``);
        the lab only ever redirects to it with a ``login_state``.
        """
        return f"{Settings.get_front_url().rstrip('/')}/{CONSENT_PAGE_ROUTE}"

    @classmethod
    def set_provider(cls, provider: LabOAuthProvider) -> None:
        """Register the provider built at startup."""
        cls._provider = provider

    @classmethod
    def get_provider(cls) -> LabOAuthProvider:
        """Return the provider, or raise if the lab was not initialized."""
        if cls._provider is None:
            raise RuntimeError(
                "The OAuth provider is not initialized (mount_mcp_app was not called)."
            )
        return cls._provider

    @classmethod
    def has_provider(cls) -> bool:
        return cls._provider is not None

    @classmethod
    def clear(cls) -> None:
        """Drop the provider. Useful for tests."""
        cls._provider = None
