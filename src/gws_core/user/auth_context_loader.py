"""Auth context loaders for different runtime environments.

Each loader implements a storage strategy for authentication contexts
in different environments (HTTP, Streamlit, Reflex, etc.).
"""

from abc import ABC, abstractmethod

from starlette_context import context

from gws_core.core.utils.http_helper import HTTPHelper
from gws_core.user.auth_context import AuthContextBase


class AuthContextLoader(ABC):
    """Abstract base class for auth context storage strategies.

    Each loader is responsible for storing and retrieving auth contexts
    in its specific runtime environment.
    """

    @abstractmethod
    def get(self) -> AuthContextBase | None:
        """Retrieve the auth context from storage.

        Returns:
            The stored auth context, or None if not set.
        """
        pass

    @abstractmethod
    def set(self, auth_context: AuthContextBase | None) -> None:
        """Store the auth context.

        Args:
            auth_context: The auth context to store, or None to clear.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the auth context from storage."""
        pass


class DefaultAuthContextLoader(AuthContextLoader):
    """Loader for HTTP/FastAPI context using Starlette request context.

    Uses starlette_context for request-scoped storage.

    If not in an HTTP context, falls back to in-memory storage.
    """

    _STORAGE_KEY = "auth_context"

    _no_http_auth_context: AuthContextBase | None = None

    def get(self) -> AuthContextBase | None:
        if HTTPHelper.is_http_context():
            return context.data.get(self._STORAGE_KEY)
        else:
            return self._no_http_auth_context

    def set(self, auth_context: AuthContextBase | None) -> None:
        if HTTPHelper.is_http_context():
            context.data[self._STORAGE_KEY] = auth_context
        else:
            self._no_http_auth_context = auth_context

    def clear(self) -> None:
        self.set(None)
