

import os
from json import load
from typing import Any, Callable

import streamlit as st
import streamlit.components.v1 as components
from fastapi.encoders import jsonable_encoder

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    LoggerMessageObserver
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.streamlit.widgets.streamlit_helper import StreamlitHelper
from gws_core.streamlit.widgets.streamlit_state import StreamlitUserAuthInfo


class StreamlitComponentLoader():
    """ Class to load a streamlit component.
    In dev mode
        - the component is loaded from the dev front app running in (DEV_FRONT_URL).
    In release mode
        - the IFRAME_MESSAGE is downloaded from the github release.
        - then the comopnent is generated as streamlit component.
        - the IFRAME_MESSAGE role is to send message to streamlit app to generate the component in main app.

    :return: _description_
    :rtype: _type_
    """

    VERSION_FILE_NAME = "version.json"
    VERSION_KEY = "version"

    RELEASE_BASE_URL = 'https://github.com/Constellab/dashboard-components/releases/download/'

    IFRAME_MESSAGE = "iframe-message"
    IFRAME_MESSAGE_VERSION = "dc_iframe_message_1.2.0"

    IS_RELEASED = False
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
            timestamp=DateHelper.now_utc_as_milliseconds()
        )

    def get_function(self) -> Callable:
        # use dev mode only in local environment and is not released
        if not Settings.is_local_env() or self.IS_RELEASED:
            return self._get_released_function()
        else:
            return self._get_dev_function()

    def _get_dev_function(self) -> Callable:
        return components.declare_component(
            self.component_name,
            url=self.DEV_FRONT_URL,
        )

    def _get_released_function(self) -> Callable:
        """ Load the component in release mode.
        The iframe message component is loaded from the github release.
        The


        :return: _description_
        :rtype: Callable
        """

        settings = Settings.get_instance()
        destination_folder = settings.get_brick_data_dir(BrickHelper.GWS_CORE)

        # read the existing version
        destination_folder_full_path = os.path.join(destination_folder, self.IFRAME_MESSAGE_VERSION)
        existing_version = self._get_existing_version(destination_folder_full_path)

        if existing_version == self.IFRAME_MESSAGE_VERSION:
            # The component is already downloaded
            return components.declare_component(
                self.component_name,
                path=destination_folder_full_path,
            )

        # Delete the existing component
        FileHelper.delete_dir(destination_folder_full_path)

        message_dispatcher = MessageDispatcher()
        message_dispatcher.attach(LoggerMessageObserver())

        # Download the file
        folder_path: str
        with st.spinner('Installing the component...'):
            Logger.info(f"Downloading the component {self.component_name} version {self.IFRAME_MESSAGE_VERSION}")
            file_downloader = FileDownloader(destination_folder, message_dispatcher=message_dispatcher)
            folder_path = file_downloader.download_file_if_missing(self._get_release_url(), self.IFRAME_MESSAGE_VERSION,
                                                                   decompress_file=True)

        return components.declare_component(
            self.component_name,
            path=folder_path,
        )

    def _get_existing_version(self, destination_folder: str) -> str | None:
        try:
            if FileHelper.exists_on_os(destination_folder):
                # read the version from the file
                version_file_path = os.path.join(destination_folder, self.VERSION_FILE_NAME)
                with open(version_file_path, 'r', encoding='UTF-8') as file:
                    version_json = load(file)
                    return version_json.get(self.VERSION_KEY)
        except Exception as e:
            Logger.error(f"Error reading the version file: {e}")
        return None

    def _get_release_url(self) -> str:
        return f"{self.RELEASE_BASE_URL}{self.IFRAME_MESSAGE_VERSION}/{self.IFRAME_MESSAGE}.zip"
