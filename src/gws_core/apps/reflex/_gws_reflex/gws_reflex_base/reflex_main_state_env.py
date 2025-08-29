from typing import List

from .reflex_main_state_base_2 import ReflexMainStateBase2


class ReflexMainStateEnv(ReflexMainStateBase2):
    """Main State of Reflex virtual env app. This state is in virtual environment app where gws_core is not loaded.

    It provides a method to access the paths of the input resources of the app.
    """

    async def get_source_paths(self) -> List[str]:
        """Return the resources of the app."""
        return await self.get_sources_ids()
