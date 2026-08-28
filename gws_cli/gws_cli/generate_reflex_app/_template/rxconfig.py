import os

import reflex as rx

# [START_AUTO_CODE]
# Code to load gws_core environment and initialize the main state.
# DO NOT MODIFY THIS CODE UNLESS YOU KNOW WHAT YOU ARE DOING.


def _init_reflex(config: rx.Config) -> None:
    """Initialize Reflex environment after config is created to avoid circular imports."""
    # Import inside the function to avoid circular import
    from gws_reflex_base import ReflexInit, get_theme  # noqa: PLC0415

    # Call init but ignore the return value since we already got api_url
    ReflexInit.init()

    # Configure the GWS theme via RadixThemesPlugin (replaces the deprecated
    # App(theme=...), removed in reflex 1.0). Done here because get_theme is only
    # importable once ReflexInit.init() has set up the gws_reflex_base path.
    config.plugins.append(
        rx.plugins.RadixThemesPlugin(theme=get_theme()),
    )


api_url = os.environ.get("GWS_REFLEX_API_URL")
if api_url is None:
    raise ValueError("GWS_REFLEX_API_URL environment variable is not set")
# [END_AUTO_CODE]

config = rx.Config(
    app_name="{{APP_NAME}}",
    plugins=[
        rx.plugins.SitemapPlugin(),
    ],
    # [START_AUTO_CODE]
    api_url=api_url,
    # [END_AUTO_CODE]
)

# [START_AUTO_CODE]
# Now that config exists, call initialization
# This must happen after config is defined to avoid circular imports
_init_reflex(config)
# [END_AUTO_CODE]
