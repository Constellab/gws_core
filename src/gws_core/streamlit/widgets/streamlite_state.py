import streamlit as st

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.user.user import User


class StreamlitUserAuthInfo(BaseModelDTO):
    app_id: str
    user_access_token: str


class StreamlitState():

    @classmethod
    def get_current_user(cls) -> User | None:
        """ Return the current connected user. If no user is connected, return None

        :return: the current connected user
        :rtype: User | None
        """
        return st.session_state.get('__gws_user__')

    @classmethod
    def set_current_user(cls, user: User) -> None:
        """ Set the current connected user

        :param user: the user to set as current
        :type user: User
        """
        st.session_state['__gws_user__'] = user

    @classmethod
    def app_requires_authentication(cls) -> bool:
        """ Return if the app requires authentication

        :return: if the app requires authentication
        :rtype: bool
        """
        return st.session_state.get('__gws_requires_authentication__')

    @classmethod
    def set_app_requires_authentication(cls, requires_authentication: bool) -> None:
        """ Set if the app requires authentication

        :param requires_authentication: if the app requires authentication
        :type requires_authentication: bool
        """
        st.session_state['__gws_requires_authentication__'] = requires_authentication

    @classmethod
    def get_app_id(cls) -> str:
        """ Return the app id

        :return: the app id
        :rtype: str | None
        """
        gws_app_id = st.query_params.get('gws_app_id')
        if not gws_app_id:
            st.error('App id not provided')
            st.stop()
        return gws_app_id

    @classmethod
    def get_user_access_token(cls) -> str:
        """ Return the user access token

        :return: the user access token
        :rtype: str | None
        """
        user_access_token = st.query_params.get('gws_user_access_token')
        if not user_access_token:
            st.error('User access token not provided')
            st.stop()
        return user_access_token

    @classmethod
    def get_user_auth_info(cls) -> StreamlitUserAuthInfo:
        """ Return the user auth info.
        This is useful to auth the user in custom components

        :return: the user auth info
        :rtype: StreamlitUserAuthInfo
        """
        return StreamlitUserAuthInfo(app_id=cls.get_app_id(), user_access_token=cls.get_user_access_token())
