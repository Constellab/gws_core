import contextvars

from gws_core.user.auth_context import AuthContextBase
from gws_core.user.auth_context_loader import AuthContextLoader


class ReflexAuthContextLoader(AuthContextLoader):
    """Loader for Reflex apps using contextvars.

    Uses contextvars for async-safe, per-request context isolation.
    This is thread-safe and works well with Reflex's async event handling.
    """

    AAAAA: str = "SUPER"

    _context_var: contextvars.ContextVar[AuthContextBase | None] = contextvars.ContextVar(
        "reflex_auth_context", default=None
    )

    def get(self) -> AuthContextBase | None:
        return self._context_var.get()

    def set(self, auth_context: AuthContextBase | None) -> None:
        self._context_var.set(auth_context)

    def clear(self) -> None:
        self._context_var.set(None)
