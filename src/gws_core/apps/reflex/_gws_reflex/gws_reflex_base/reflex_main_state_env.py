
from .reflex_main_state_base import ReflexMainStateBase


class ReflexMainStateEnv(ReflexMainStateBase):
    """Main State of Reflex virtual env app. This state is in virtual environment app where gws_core is not loaded.

    It provides a method to access the paths of the input resources of the app.
    """

    async def get_source_paths(self) -> list[str]:
        """Return the resources of the app."""
        return await self.get_sources_ids()
