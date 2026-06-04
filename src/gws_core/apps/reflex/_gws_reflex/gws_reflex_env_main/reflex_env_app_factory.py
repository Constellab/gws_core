"""
Helper function to apply GWS standard configuration to Reflex applications.
"""

import reflex as rx
from gws_reflex_base import (
    ReflexMainStateBaseFactory,
    default_gws_env_backend_handler,
    default_gws_env_frontend_handler,
)
from gws_reflex_base import add_unauthorized_page as _add_unauthorized_page
from reflex.app import default_backend_exception_handler, default_frontend_exception_handler

from .reflex_main_state_env import ReflexMainStateEnv


def register_gws_reflex_env_app(
    app: rx.App | None = None, add_unauthorized_page: bool = True
) -> rx.App:
    """
    Apply GWS standard configuration to a Reflex app in a virtual environment.

    This function modifies the app in-place by setting GWS defaults for any
    parameters that are not already defined. If no app is provided, a new one
    is created. This allows you to create your app normally with rx.App() and
    have full IDE support, then apply GWS standards with a simple function call.

    Standard GWS defaults applied (if not already set):
    - theme: configured via ``RadixThemesPlugin(theme=get_theme())`` in the app's
      ``rxconfig.py`` (light/dark mode based on environment)
    - frontend_exception_handler: Logs exceptions
    - backend_exception_handler: Shows toast notifications with error details
    - unauthorized_page: Adds the unauthorized route (if add_unauthorized_page=True)

    Example usage:
    ```python
    from gws_reflex_base import register_gws_reflex_app

    # Option 1: Create app with defaults
    app = register_gws_reflex_app()

    # Option 2: Create app with custom params, then apply defaults
    app = rx.App(
        html_lang="fr",  # Full IDE support for all rx.App parameters
        reset_style=False,
    )
    register_gws_reflex_app(app)

    # Option 3: Skip the unauthorized page
    app = register_gws_reflex_app(add_unauthorized_page=False)
    ```

    :param app: The Reflex app instance to configure (creates new if None)
    :type app: Optional[rx.App]
    :param add_unauthorized_page: Whether to add the unauthorized page route (default: True)
    :type add_unauthorized_page: bool
    :return: The configured app instance
    :rtype: rx.App
    """

    ReflexMainStateBaseFactory.set_main_state_class(ReflexMainStateEnv)
    # Create app if not provided. The theme is configured via
    # RadixThemesPlugin(theme=get_theme()) in the app's rxconfig.py, not here
    # (App(theme=...) was deprecated in reflex 0.9.0).
    if app is None:
        app = rx.App()

    # Register the exception handlers (only if still using the reflex defaults)
    if (
        not app.frontend_exception_handler
        or app.frontend_exception_handler == default_frontend_exception_handler
    ):
        app.frontend_exception_handler = default_gws_env_frontend_handler

    if (
        not app.backend_exception_handler
        or app.backend_exception_handler == default_backend_exception_handler
    ):
        app.backend_exception_handler = default_gws_env_backend_handler

    # Add unauthorized page if requested
    if add_unauthorized_page:
        _add_unauthorized_page(app)

    return app
