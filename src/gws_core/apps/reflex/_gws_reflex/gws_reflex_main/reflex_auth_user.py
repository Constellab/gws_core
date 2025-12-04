from gws_core.user.auth_context import AuthContextApp
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


class ReflexAuthUser:
    auth_context: AuthContextApp
    was_already_authenticated: bool = False

    def __init__(self, auth_context: AuthContextApp):
        self.auth_context = auth_context

    def __enter__(self) -> User:
        CurrentUserService.set_reflex_context()

        if CurrentUserService.get_current_user() is None:
            CurrentUserService.set_auth_context(self.auth_context)
        else:
            if CurrentUserService.get_current_user().id != self.auth_context.user.id:
                raise Exception("The user in the context is different from the current user")
            self.was_already_authenticated = True

        return self.auth_context.user

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.was_already_authenticated:
            CurrentUserService.clear_auth_context()

        # raise the exception if exists
        if exc_value:
            raise exc_value
