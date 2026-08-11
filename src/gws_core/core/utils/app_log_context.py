from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

# Context variable holding the id of the app an operation is performed for.
# Set by app operations running in the server process (start, build, stop, nginx
# registration, plugin install) so their MAIN-context log records carry the app id.
_app_context_id_ctx: ContextVar[str | None] = ContextVar("app_context_id", default=None)


class AppLogContext:
    """Provides the app id to attach to log records emitted by the server process.

    The log formatter uses it as the `context_id` of MAIN-context records, so
    everything the server does *for* an app (frontend build, cache clear, nginx
    registration, plugin install) can be attributed to that app — the same way the
    app's own child process tags its records via the REFLEX/STREAMLIT context.

    Note that `ContextVar` values do not propagate into `threading.Thread` targets:
    a thread that must inherit the value has to be started through
    `contextvars.copy_context().run` (see `ShellProxy.run_in_new_thread`).
    """

    @classmethod
    def get_context_id(cls) -> str | None:
        """Get the current app context id, or None if not in an app operation."""
        return _app_context_id_ctx.get()

    @classmethod
    def set_context_id(cls, context_id: str | None) -> None:
        """Set the app context id for the current context."""
        _app_context_id_ctx.set(context_id)

    @classmethod
    def clear(cls) -> None:
        """Clear the app context id from the current context."""
        _app_context_id_ctx.set(None)

    @classmethod
    @contextmanager
    def use(cls, context_id: str) -> Iterator[None]:
        """Context manager to set the app context id for a block of code."""
        token = _app_context_id_ctx.set(context_id)
        try:
            yield
        finally:
            _app_context_id_ctx.reset(token)
