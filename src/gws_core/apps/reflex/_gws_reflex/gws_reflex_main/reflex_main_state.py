from typing import List

from gws_reflex_base import ReflexMainStateBase

from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel


class ReflexMainState(ReflexMainStateBase):
    """Main state for the normal (not in virtual environment) Reflex app. extending the base state with resource management.

    It provides methods to access the input resources of the app.

    """

    def get_resources(self) -> List[Resource]:
        """Return the resources of the app."""
        if not self.is_initialized:
            return []

        sources_ = []
        for source_path in self.get_sources_ids():
            resource_model = ResourceModel.get_by_id_and_check(source_path)
            sources_.append(resource_model.get_resource())
        return sources_
