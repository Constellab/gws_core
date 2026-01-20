import json
from enum import Enum

import streamlit as st

from gws_core.core.utils.logger import Logger


class StreamlitTranslateLang(Enum):
    """Enum to define supported languages for translation."""

    FR = "fr"  # French
    EN = "en"  # English


class StreamlitTranslateService:
    """
    Service class to handle translations in Streamlit applications.

    Attributes:
        lang (StreamlitTranslateLang): The current language in use.
        translation_dict (dict): Dictionary containing translation key-value pairs.
        translation_files_folder_path (str): Path to the folder containing translation files.
    """

    lang: StreamlitTranslateLang
    translation_dict: dict
    translation_files_folder_path: str

    def __init__(
        self,
        translation_files_folder_path: str,
        lang_: StreamlitTranslateLang = StreamlitTranslateLang.EN,
    ):
        """
        Initialize the translation service.

        Args:
            translation_files_folder_path (str): Path to the folder containing translation files (en.json and fr.json by default).
            lang_ (StreamlitTranslateLang): Default language for translations (default is English).
        """
        if "selected_lang" in st.session_state:
            self.lang = st.session_state.selected_lang
        else:
            st.session_state.selected_lang = lang_
            self.lang = lang_
        self.translation_files_folder_path = translation_files_folder_path
        self._set_translation_dict()

    def _set_translation_dict(self) -> None:
        """
        Load the translation dictionary from a JSON file.

        Raises:
            FileNotFoundError: If the translation file for the specified language is not found.
        """
        with open(
            f"{self.translation_files_folder_path}/{self.lang.value}.json", encoding="utf-8"
        ) as json_file:
            self.translation_dict = json.load(json_file)
            json_file.close()

    def change_lang(self, lang_: StreamlitTranslateLang) -> None:
        """
        Change the current language and reload the translation dictionary.

        Args:
            lang_ (StreamlitTranslateLang): The new language to switch to.
        """

        self._set_translation_dict()
        self.lang = lang_
        st.session_state.selected_lang = lang_
        st.rerun(scope="app")

    def get_lang(self) -> StreamlitTranslateLang:
        """
        Get the current language.

        Returns:
            StreamlitTranslateLang: The current language.
        """
        return self.lang

    def translate(self, key: str) -> str:
        """
        Translate a given key into the current language.

        Args:
            key (str): The key to translate.

        Returns:
            str: The translated value corresponding to the key.

        Raises:
            Exception: If the key is not found in the translation dictionary.
        """
        if key not in self.translation_dict:
            Logger.warning(f"No translation for key: {key}")
            return key
        return self.translation_dict[key]
