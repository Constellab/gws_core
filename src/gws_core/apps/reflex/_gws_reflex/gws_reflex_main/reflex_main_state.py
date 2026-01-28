import reflex as rx
from gws_reflex_base import ReflexMainStateBase
from gws_reflex_main.reflex_user_auth import ReflexUserAuthInfo

from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.auth_context import AuthContextApp
from gws_core.user.user import User

from .reflex_auth_user import ReflexAuthUser


class ReflexMainState(ReflexMainStateBase, rx.State):
    """Main state for the normal (not in virtual environment) Reflex app. extending the base state with resource management.

    It provides methods to access the input resources of the app.
    """

    async def _on_initialized(self) -> None:
        """Called when the base state has finished initialization.

        Override this method in subclasses to perform actions after initialization.
        """
        pass

    async def get_resources(self) -> list[Resource]:
        """Return the resources of the app."""

        sources_ = []
        for source_path in await self.get_sources_ids():
            resource_model = ResourceModel.get_by_id_and_check(source_path)
            sources_.append(resource_model.get_resource())
        return sources_

    async def get_current_user(self) -> User | None:
        """Return the current user of the app."""
        if not self._is_initialized:
            await self._on_load()

        user_id = self.authenticated_user_id
        if not user_id:
            return None
        return User.get_by_id_and_check(user_id)

    async def get_and_check_current_user(self) -> User:
        """Get the current user and check if it is authenticated.
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

    @rx.var
    async def get_reflex_user_auth_info(self) -> ReflexUserAuthInfo:
        """Get the Reflex user authentication info.

        Returns:
            ReflexUserAuthInfo: The Reflex user authentication info.
        """
        user_access_token = self._get_user_access_token()
        if not user_access_token:
            raise Exception("User access token not found")
        return ReflexUserAuthInfo(app_id=self.get_app_id(), user_access_token=user_access_token)
