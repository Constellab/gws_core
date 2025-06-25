

from gws_core.streamlit.widgets.streamlit_state import StreamlitState
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


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
        user = StreamlitState.get_current_user()
        if user is None:
            raise Exception("There is no user in the streamlit context")
        if CurrentUserService.get_current_user() is None:
            CurrentUserService.set_current_user(user)
        else:
            if CurrentUserService.get_current_user().id != user.id:
                raise Exception("The user in the context is different from the current user")
            self.was_already_authenticated = True

        # Set streamlit context
        CurrentUserService.set_app_context()
        return user

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.was_already_authenticated:
            CurrentUserService.set_current_user(None)

        # raise the exception if exists
        if exc_value:
            raise exc_value
