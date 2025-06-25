from typing import List

from .reflex_main_state_base import ReflexMainStateBase


class ReflexMainStateEnv(ReflexMainStateBase):
    """Main State of Reflex virtual env app. This state is in virtual environment app where gws_core is not loaded.

    It provides a method to access the paths of the input resources of the app.
    """

    def get_source_paths(self) -> List[str]:
        """Return the resources of the app."""
        if not self.is_initialized:
            return []
        return self.get_sources_ids()
