

import os
from json import load
from typing import Callable

import streamlit as st
import streamlit.components.v1 as components

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    LoggerMessageObserver
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class StreamlitComponentLoader():

    # url for dev front app
    DEV_FRONT_URL = "http://localhost:4200"

    VERSION_FILE_NAME = "version.json"
    VERSION_KEY = "version"

    RELEASE_BASE_URL = 'https://github.com/Constellab/dashboard-components/releases/download/'

    component_name: str
    version: str
    is_released: bool

    def __init__(self, component_name: str, version: str, is_released: bool):
        self.component_name = component_name
        self.version = version
        self.is_released = is_released

    def get_function(self) -> Callable:
        if self.is_released:
            return self._get_released_function()
        else:
            return self._get_dev_function()

    def _get_dev_function(self) -> Callable:
        return components.declare_component(
            self.component_name,
            url=self.DEV_FRONT_URL,
        )

    def _get_released_function(self) -> Callable:

        settings = Settings.get_instance()
        destination_folder = settings.get_brick_data_dir(BrickHelper.GWS_CORE)

        # read the existing version
        destination_folder_full_path = os.path.join(destination_folder, self.version)
        existing_version = self._get_existing_version(destination_folder_full_path)

        if existing_version == self.version:
            # The component is already downloaded
            return components.declare_component(
                self.component_name,
                path=destination_folder_full_path,
            )

        # Delete the existing component
        FileHelper.delete_dir(destination_folder)

        message_dispatcher = MessageDispatcher()
        message_dispatcher.attach(LoggerMessageObserver())

        # Download the file
        folder_path: str
        with st.spinner('Downloading the component...'):
            Logger.info(f"Downloading the component {self.component_name} version {self.version}")
            file_downloader = FileDownloader(destination_folder, message_dispatcher=message_dispatcher)
            folder_path = file_downloader.download_file_if_missing(self._get_release_url(), self.version,
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
        return f"{self.RELEASE_BASE_URL}{self.version}/{self.component_name}.zip"
