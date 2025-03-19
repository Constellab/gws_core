
import streamlit as st

from gws_core.user.current_user_service import CurrentUserService


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

    def __enter__(self):
        user = st.session_state.get('__gws_user__')
        if user is None:
            raise Exception("There is no user in the context")
        if CurrentUserService.get_current_user() is None:
            CurrentUserService.set_current_user(user)
        else:
            if CurrentUserService.get_current_user().id != user.id:
                raise Exception("The user in the context is different from the current user")
            self.was_already_authenticated = True

        # Set streamlit context
        CurrentUserService.set_streamlit_context()
        # Code to set up and acquire resources
        return self  # You can return an object that you want to use in the with block

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.was_already_authenticated:
            CurrentUserService.set_current_user(None)

        # raise the exception if exists
        if exc_value:
            raise exc_value
