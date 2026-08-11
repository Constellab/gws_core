# The ReflexPlugin class lives in gws_core so the server process can install the
# plugin without importing the reflex components package. Re-exported here because
# apps import it from gws_reflex_main.
from gws_core.apps.reflex.reflex_plugin import ReflexPlugin

__all__ = ["ReflexPlugin"]
