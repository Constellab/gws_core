from typing import List, Optional

from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.user import User
from gws_reflex_base import ReflexMainStateBase


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

    def get_current_user(self) -> Optional[User]:
        """Return the current user of the app."""
        # in dev mode we load the system user by default
        # if authentication is enabled

        user_id = self.authenticated_user_id
        if not user_id:
            return None
        return User.get_by_id_and_check(user_id)

    def get_and_check_current_user(self) -> User:
        user = self.get_current_user()
        if not user:
            raise Exception("User not authenticated")
        return user
