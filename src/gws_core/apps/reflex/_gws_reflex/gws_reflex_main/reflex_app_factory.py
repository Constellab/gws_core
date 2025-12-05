"""
Helper function to apply GWS standard configuration to Reflex applications.
"""


import reflex as rx
from gws_reflex_base import ReflexMainStateBase, get_theme
from gws_reflex_base import add_unauthorized_page as _add_unauthorized_page
from reflex.app import default_backend_exception_handler, default_frontend_exception_handler

from gws_core.core.exception.exceptions.base_http_exception import BaseHTTPException
from gws_core.core.utils.logger import Logger


def default_gws_frontend_handler(exception: Exception) -> None:
    """Default frontend exception handler for GWS apps.

    :param exception: The exception that occurred
    :type exception: Exception
    """
    Logger.log_exception_stack_trace(exception)


def default_gws_backend_handler(
    exception: Exception,
) -> rx.event.EventSpec | None:
    """Default backend exception handler for GWS apps.

    :param exception: The exception that occurred
    :type exception: Exception
    :return: Event spec to show error toast
    :rtype: Optional[rx.event.EventSpec]
    """
    if isinstance(exception, BaseHTTPException):
        return rx.toast.error(exception.get_detail_with_args(), position="top-center")

    Logger.log_exception_stack_trace(exception)

    if ReflexMainStateBase.is_dev_mode():
        # In dev mode, show the full error message
        return rx.toast.error(
            f"An unexpected error occurred: {str(exception)}", position="top-center"
        )

    # In production mode, show a generic error message
    return rx.toast.error("An unexpected error occurred.", position="top-center")


def register_gws_reflex_app(
    app: rx.App | None = None, add_unauthorized_page: bool = True
) -> rx.App:
    """
    Apply GWS standard configuration to a Reflex app.

    This function modifies the app in-place by setting GWS defaults for any
    parameters that are not already defined. If no app is provided, a new one
    is created. This allows you to create your app normally with rx.App() and
    have full IDE support, then apply GWS standards with a simple function call.

    Standard GWS defaults applied (if not already set):
    - theme: Teal accent color with light/dark mode based on environment
    - stylesheets: ["/style.css"]
    - frontend_exception_handler: Logs exceptions using GWS Logger
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
    # Create app if not provided
    if app is None:
        app = rx.App()

    # Apply GWS
    app.theme = get_theme()

    if not app.stylesheets:
        app.stylesheets = ["/style.css"]

    # Check if using default exception handlers (compare functions, not instances)

    if (
        not app.frontend_exception_handler
        or app.frontend_exception_handler == default_frontend_exception_handler
    ):
        app.frontend_exception_handler = default_gws_frontend_handler

    if (
        not app.backend_exception_handler
        or app.backend_exception_handler == default_backend_exception_handler
    ):
        app.backend_exception_handler = default_gws_backend_handler

    # Add unauthorized page if requested
    if add_unauthorized_page:
        _add_unauthorized_page(app)

    return app
