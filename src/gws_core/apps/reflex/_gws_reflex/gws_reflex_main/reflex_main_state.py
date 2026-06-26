import reflex as rx
from gws_reflex_base import ReflexMainStateBase
from gws_reflex_main.reflex_user_auth import ReflexUserAuthInfo

from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
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

        user_id = await self._load_and_check_user_authentication(store_in_state=False)
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
            raise BadRequestException("User not authenticated")
        return user

    async def authenticate_user(self) -> ReflexAuthUser:
        user = await self.get_and_check_current_user()
        app_id = self.get_app_id()
        auth_context = AuthContextApp(app_id=app_id, user=user)
        return ReflexAuthUser(auth_context)

    async def _build_user_auth_info(
        self, fallback_to_system_user: bool
    ) -> ReflexUserAuthInfo | None:
        """Build the auth info a front component needs to call the data lab API.

        Uses the authenticated user's access token when available. When no user is
        authenticated (PUBLIC app) and ``fallback_to_system_user`` is True, falls back to the
        system user's access token so the front can still reach the API. Returns None when no
        token is available (PUBLIC app, no user, no fallback).
        """
        user_access_token = self._get_user_access_token()

        if not user_access_token and fallback_to_system_user:
            user_access_token = await self._get_system_user_access_token()

        if not user_access_token:
            return None
        return ReflexUserAuthInfo(app_id=self.get_app_id(), user_access_token=user_access_token)

    @rx.var
    async def get_reflex_user_auth_info(self) -> ReflexUserAuthInfo | None:
        """Get the Reflex user authentication info for the authenticated user.

        Returns None when no user is authenticated (PUBLIC app). Components bound to this var
        will not be able to call the data lab API in that case; use
        ``get_reflex_user_auth_info_with_system_fallback`` (via the component's
        ``fallback_to_system_user`` option) to run those requests as the system user instead.

        Returns:
            ReflexUserAuthInfo | None: The Reflex user authentication info, or None.
        """
        return await self._build_user_auth_info(fallback_to_system_user=False)

    @rx.var
    async def get_reflex_user_auth_info_with_system_fallback(self) -> ReflexUserAuthInfo | None:
        """Like ``get_reflex_user_auth_info`` but falls back to the system user.

        When no user is authenticated (PUBLIC app), this returns the system user's auth info
        so the bound component can still call the data lab API. WARNING: this lets any visitor
        of the app read and write data lab objects through the API as the system user. Only
        use it (via a component's ``fallback_to_system_user`` option) on apps where this is
        acceptable.

        Returns:
            ReflexUserAuthInfo | None: The Reflex user authentication info, or None.
        """
        return await self._build_user_auth_info(fallback_to_system_user=True)
