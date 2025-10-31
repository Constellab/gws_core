from typing import List, Optional

from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.auth_context import AuthContextApp
from gws_core.user.user import User
from gws_reflex_base import ReflexMainStateBase

from .reflex_auth_user import ReflexAuthUser


class ReflexMainState(ReflexMainStateBase):
    """Main state for the normal (not in virtual environment) Reflex app. extending the base state with resource management.

    It provides methods to access the input resources of the app.
    """

    async def get_resources(self) -> List[Resource]:
        """Return the resources of the app."""

        sources_ = []
        for source_path in await self.get_sources_ids():
            resource_model = ResourceModel.get_by_id_and_check(source_path)
            sources_.append(resource_model.get_resource())
        return sources_

    async def get_current_user(self) -> Optional[User]:
        """Return the current user of the app."""
        # in dev mode we load the system user by default
        # if authentication is enabled

        if not self._is_initialized:
            await self._on_load()

        user_id = self.authenticated_user_id
        if not user_id:
            return None
        return User.get_by_id_and_check(user_id)

    async def get_and_check_current_user(self) -> User:
        """ Get the current user and check if it is authenticated.
        Don't call this method in a @rx.var, use get_current_user instead (because it will fail during build).
        Use this method in @rx.event or other methods only.

        Raises:
            Exception: If the user is not authenticated.

        Returns:
            User: The current user.
        """
        user = await self.get_current_user()

        if not user:
            raise Exception("User not authenticated")
        return user

    async def authenticate_user(self) -> ReflexAuthUser:
        user = await self.get_and_check_current_user()
        app_id = self.get_app_id()
        auth_context = AuthContextApp(app_id=app_id, user=user)
        return ReflexAuthUser(auth_context)
