# The component are exported at this level to only load them when they are used
# Because it triggers the loading of the reflex_plugin that load js assets
from .reflex_rich_text_component.reflex_rich_text_component import \
    rich_text_component as rich_text_component


def __load_plugins__():
    """Load the required plugins for the components."""
    from ..reflex_plugin import ReflexPlugin
    reflex_component = ReflexPlugin()
    reflex_component.install_package()


# Load plugins when this module is imported
__load_plugins__()
