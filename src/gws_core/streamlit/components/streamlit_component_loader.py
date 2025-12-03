from collections.abc import Callable
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from fastapi.encoders import jsonable_encoder

from gws_core.apps.app_plugin_downloader import AppPluginDownloader
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.streamlit.widgets.streamlit_helper import StreamlitHelper
from gws_core.streamlit.widgets.streamlit_state import StreamlitUserAuthInfo


class StreamlitComponentLoader:
    """Class to load a streamlit component.
    In dev mode
        - the component is loaded from the dev front app running in (DEV_FRONT_URL).
    In release mode
        - the IFRAME_MESSAGE is downloaded from the github release using ComponentPackageDownloader.
        - then the component is generated as streamlit component.
        - the IFRAME_MESSAGE role is to send message to streamlit app to generate the component in main app.

    :return: _description_
    :rtype: _type_
    """

    IS_RELEASED = True
    # url for dev front app
    DEV_FRONT_URL = "http://localhost:4201"

    # name of the component to load
    component_name: str

    def __init__(self, component_name: str):
        self.component_name = component_name

    def call_component(self, data: Any, key: str, authentication_info: StreamlitUserAuthInfo = None) -> Any:
        """Call the component with the data.

        :param data: data to pass to the component
        :type data: Any
        :param key: streamlit key
        :type key: str
        :param authenticationInfo: authentication info to pass to the component if the component can request the API, defaults to None
        :type authenticationInfo: StreamlitUserAuthInfo, optional
        :return: _description_
        :rtype: Any
        """
        return self.get_function()(
            authentication_info=authentication_info.to_json_dict() if authentication_info else None,
            container_class=StreamlitHelper.get_element_css_class(key),
            # We pass the component name to the component to be able to
            # dynamically load the component
            component=self.component_name,
            component_data=jsonable_encoder(data),
            # we pass the key so streamlit knows the component
            # key and set a class to the component container
            key=key,
            timestamp=DateHelper.now_utc_as_milliseconds(),
        )

    def get_function(self) -> Callable:
        # use dev mode only in local environment and is not released
        if not Settings.is_local_dev_env() or self.IS_RELEASED:
            return self._get_released_function()
        else:
            return self._get_dev_function()

    def _get_dev_function(self) -> Callable:
        Logger.info(f"Loading dev component: {self.component_name} from {self.DEV_FRONT_URL}")

        return components.declare_component(
            self.component_name,
            url=self.DEV_FRONT_URL,
        )

    def _get_released_function(self) -> Callable:
        """Load the component in release mode.
        The iframe message component is loaded from the github release using ComponentPackageDownloader.

        :return: _description_
        :rtype: Callable
        """

        # Download the iframe-message package using ComponentPackageDownloader
        with st.spinner("Installing the component..."):
            downloader = AppPluginDownloader(AppPluginDownloader.IFRAME_MESSAGE)
            folder_path = downloader.install_package()

        return components.declare_component(
            self.component_name,
            path=folder_path,
        )
