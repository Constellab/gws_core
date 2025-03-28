from typing import Any, Dict, List, TypedDict

import streamlit as st


class StreamlitAppInfo(TypedDict):
    app_id: str
    user_access_token: str
    requires_authentication: bool
    user_id: str
    sources: List[Any]
    source_paths: List[str]
    params: Dict[str, Any]


class StreamlitAppInfoState():

    APP_INFO_KEY = '__gws_app_info__'

    @classmethod
    def is_initialized(cls) -> bool:
        return st.session_state.get(cls.APP_INFO_KEY) is not None

    @classmethod
    def get_app_info(cls) -> StreamlitAppInfo:
        if not cls.is_initialized():
            raise Exception('App info not initialized')
        return st.session_state.get(cls.APP_INFO_KEY)

    @classmethod
    def set_app_info(cls, app_info: StreamlitAppInfo) -> None:
        st.session_state[cls.APP_INFO_KEY] = app_info
