"""
Helper function to apply GWS standard configuration to Reflex applications.
"""

from typing import Optional

import reflex as rx
from gws_reflex_base import add_unauthorized_page as _add_unauthorized_page
from gws_reflex_base import get_theme


def register_gws_reflex_env_app(app: Optional[rx.App] = None, add_unauthorized_page: bool = True) -> rx.App:
    """
    Apply GWS standard configuration to a Reflex app in a virtual environment.

    This function modifies the app in-place by setting GWS defaults for any
    parameters that are not already defined. If no app is provided, a new one
    is created. This allows you to create your app normally with rx.App() and
    have full IDE support, then apply GWS standards with a simple function call.

    Standard GWS defaults applied (if not already set):
    - theme: Teal accent color with light/dark mode based on environment
    - stylesheets: ["/style.css"]
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

    # Apply GWS defaults
    app.theme = get_theme()

    if not app.stylesheets:
        app.stylesheets = ["/style.css"]

    # Add unauthorized page if requested
    if add_unauthorized_page:
        _add_unauthorized_page(app)

    return app
