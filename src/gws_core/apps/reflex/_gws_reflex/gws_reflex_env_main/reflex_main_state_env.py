import reflex as rx
from gws_reflex_base import ReflexMainStateBase


class ReflexMainStateEnv(ReflexMainStateBase, rx.State):
    """Main State of Reflex virtual env app. This state is in virtual environment app where gws_core is not loaded.

    It provides a method to access the paths of the input resources of the app.

    It must inherit ``rx.State`` (in addition to the ``ReflexMainStateBase`` mixin) so
    that Reflex turns it into a concrete state and wraps its ``@rx.event`` methods as
    event handlers, the same way ``ReflexMainState`` does.
    """

    async def _on_initialized(self) -> None:
        """Called when the base state has finished initialization.

        Override this method in subclasses to perform actions after initialization.
        """
        pass

    async def get_source_paths(self) -> list[str]:
        """Return the resources of the app."""
        return await self.get_sources_ids()
