import streamlit as st

from gws_core.user.auth_context import AuthContextBase
from gws_core.user.auth_context_loader import AuthContextLoader


class StreamlitAuthContextLoader(AuthContextLoader):
    """Loader for Streamlit apps using session state.

    Uses st.session_state for per-session, per-user storage.
    This ensures proper isolation between different user sessions.
    """

    _STORAGE_KEY = "__gws_auth_context__"

    def get(self) -> AuthContextBase | None:
        return st.session_state.get(self._STORAGE_KEY)

    def set(self, auth_context: AuthContextBase | None) -> None:
        st.session_state[self._STORAGE_KEY] = auth_context

    def clear(self) -> None:
        if self._STORAGE_KEY in st.session_state:
            del st.session_state[self._STORAGE_KEY]
