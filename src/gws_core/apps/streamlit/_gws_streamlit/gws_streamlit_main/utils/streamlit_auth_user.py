from gws_core.user.auth_context import AuthContextApp
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User

from ..gws_streamlit_main_state import StreamlitMainState


class StreamlitAuthenticateUser:
    """Class to authenticate user in streamlit app. It authenticate the current user.
    Can be useful in part of code that are runned standalone and not in the main app. In this case, the user is not authenticated.
    Use this class to authenticate the user in the with statement like this:
    ```
    with AuthenticateUser():
        # code to run
    ```
    """

    was_already_authenticated: bool = False

    def __enter__(self) -> User:
        state_user = StreamlitMainState.get_and_check_current_user()
        if state_user is None:
            raise Exception("There is no user in the streamlit context")

        if CurrentUserService.get_current_user() is None:
            auth_context = AuthContextApp(app_id=StreamlitMainState.get_app_id(), user=state_user)
            CurrentUserService.set_auth_context(auth_context)
        else:
            if CurrentUserService.get_current_user().id != state_user.id:
                raise Exception("The user in the context is different from the current user")
            self.was_already_authenticated = True

        # Set streamlit context
        CurrentUserService.set_app_context()
        return state_user

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.was_already_authenticated:
            CurrentUserService.clear_auth_context()

        # raise the exception if exists
        if exc_value:
            raise exc_value
