import json
import os
import re
import shutil

import streamlit
from bs4 import BeautifulSoup, Comment

from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings


class StreamlitPlugin:
    """Class to install the gws_plugin in the streamlit app.
    To do this it download the plugin from the github repository
    and inject it in the streamlit index.html file.

    The plugin is used to generate custom components in the streamlit app directly
    in the app without using the iframe.
    """

    # HTML comment used to identify the start and end of injected code in index.html
    # This is used to remove previously injected code before adding new code
    START_COMMENT = '[GWS_AUTO_ADD_START]'
    END_COMMENT = '[GWS_AUTO_ADD_END]'
    # This is used to identify the plugin version in the index.html file
    VERSION_COMMENT = '[GWS_PLUGIN_VERSION]'

    # Path of the index.html folder in the streamlit package
    INDEX_HTML_FOLDER = 'static'
    INDEX_HTML = 'index.html'
    INDEX_HTML_STATIC_FOLDER = 'static'

    # Path of the injected code relative to index.html
    PLUGIN_FOLDER_NAME = 'gws_plugin'
    PLUGIN_ENVIRONMENT_FOLDER = 'assets'
    PLUGIN_ENVIRONMENT_JSON = 'environment.json'
    PLUGIN_VERSION_FILE = 'version.json'

    PLUGIN_NAME = 'streamlit-components'
    PLUGIN_VERSION = 'dc_streamlit_components_1.3.1'
    PLUGIN_BASE_URL = 'https://github.com/Constellab/dashboard-components/releases/download/'

    @classmethod
    def get_streamlit_path(cls) -> str:
        """
        Get the path to the streamlit package.
        """
        return os.path.dirname(streamlit.__file__)

    @classmethod
    def install_plugin(cls) -> None:

        installed_version = cls.get_installed_plugin_version()
        if installed_version == cls.PLUGIN_VERSION:
            Logger.debug(f"Plugin version {installed_version} is already installed.")
            return

        # if the installed version if not the same as the current version, remove the old one
        if installed_version is not None:
            Logger.info(f"Removing old plugin version {installed_version}.")
            cls.clear_plugin()
            Logger.info(f"Old plugin version {installed_version} removed.")

        try:
            # Install version
            # download the plugin from the source path
            cls._download_plugin_version()
            # In dev mode we can use the following to move a plugin pasted manually in the folder
            # shutil.move('/lab/user/bricks/gws_core/browser', cls.get_plugin_path())

            cls.modifiy_streamlit_index_html()
            cls.create_environment_json_file()
            Logger.info(f"Plugin version {cls.PLUGIN_VERSION} installed successfully.")
        except Exception as e:
            # if there is a problem with the installation, remove the plugin
            Logger.error(f"Error during plugin installation: {e}")
            cls.clear_plugin()
            raise Exception("Error during installation of gws_plugin in streamlit") from e

    @classmethod
    def get_plugin_path(cls) -> str:
        """
        Get the path to the plugin folder.
        """
        return os.path.join(
            cls.get_streamlit_html_folder_path(), cls.get_plugin_relative_path())

    @classmethod
    def get_streamlit_html_folder_path(cls) -> str:
        return os.path.join(cls.get_streamlit_path(), cls.INDEX_HTML_FOLDER)

    @classmethod
    def get_streamlit_html_file_path(cls) -> str:
        """
        Get the path to the streamlit HTML folder.
        """
        return os.path.join(cls.get_streamlit_html_folder_path(), cls.INDEX_HTML)

    @classmethod
    def get_plugin_html_file_path(cls) -> str:
        """
        Get the path to the plugin HTML folder.
        """
        return os.path.join(cls.get_plugin_path(), cls.INDEX_HTML)

    @classmethod
    def get_plugin_relative_path(cls) -> str:
        """
        Get the relative path to the plugin folder from stramlit index.html.
        """
        return os.path.join(cls.INDEX_HTML_STATIC_FOLDER, cls.PLUGIN_FOLDER_NAME)

    @classmethod
    def get_installed_plugin_version(cls) -> str | None:
        """To get the version we check the version in the index.html file and the version in the plugin folder.
        If both versions are present and match, we return the plugin version.
        If the versions do not match, we clear the plugin and return None. It is possible when
        the streamlit package is updated, the index.html file is updated but the plugin is not.
        If no version is found, we return None.

        :return: _description_
        :rtype: str | None
        """
        index_version = cls.get_version_from_index_html()

        plugin_js_version = cls.get_installed_plugin_js_version()

        if not index_version and not plugin_js_version:
            return None

        if index_version != plugin_js_version:
            Logger.warning(f"Version mismatch: index.html version '{index_version}' "
                           f"does not match installed plugin version '{plugin_js_version}'. "
                           f"Using index.html version.")
            cls.clear_plugin()
            return None

        return plugin_js_version

    @classmethod
    def get_version_from_index_html(cls) -> str | None:
        """
        Get the version of the plugin from the index.html file.
        Extract the text between the version comment tags.
        """
        index_html_path = cls.get_streamlit_html_file_path()
        if not os.path.exists(index_html_path):
            return None

        with open(index_html_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Use regex to find the version comment
            version_pattern = re.compile(
                r'<!--\s*' + re.escape(cls.VERSION_COMMENT) + r'(\S+)\s*' + re.escape(cls.VERSION_COMMENT) + r'-->')
            match = version_pattern.search(content)
            if match:
                return match.group(1)

    @classmethod
    def get_installed_plugin_js_version(cls) -> str | None:
        """
        Get the installed plugin version.
        """
        version_file_path = os.path.join(cls.get_plugin_path(), cls.PLUGIN_VERSION_FILE)
        if not os.path.exists(version_file_path):
            return None

        with open(version_file_path, 'r', encoding='utf-8') as file:
            version_data = json.load(file)
            return version_data.get('version')

    @classmethod
    def _download_plugin_version(cls) -> None:
        """
        Download the plugin version.
        """
        Logger.info(f"Downloading version {cls.PLUGIN_VERSION} of the gws streamlit plugin.")
        plugin_folder = os.path.join(cls.get_streamlit_html_folder_path(), cls.INDEX_HTML_STATIC_FOLDER)
        file_downloader = FileDownloader(plugin_folder)
        plugin_download_url = f"{cls.PLUGIN_BASE_URL}{cls.PLUGIN_VERSION}/{cls.PLUGIN_NAME}.zip"
        file_downloader.download_file_if_missing(plugin_download_url, cls.PLUGIN_FOLDER_NAME,
                                                 decompress_file=True)

        # Check if the folder was downloaded successfully
        installed_version = cls.get_installed_plugin_js_version()
        if installed_version != cls.PLUGIN_VERSION:
            raise Exception(f"Failed to download the plugin version '{cls.PLUGIN_VERSION}'. "
                            f"Installed version is '{installed_version}'.")

    @classmethod
    def create_environment_json_file(cls):
        dict_ = {
            "apiBaseUrl": Settings.get_lab_api_url(),
            "baseHref": cls.get_plugin_relative_path(),
            "spaceApiUrl": Settings.get_space_api_url(),
            "communityFrontUrl": Settings.get_community_front_url(),
            "communityApiUrl": Settings.get_community_api_url(),
        }

        # Define the path for the JSON file
        json_dir = os.path.join(cls.get_plugin_path(), cls.PLUGIN_ENVIRONMENT_FOLDER)
        # if the file doesn't exists, throw an error
        if not os.path.exists(json_dir):
            raise FileNotFoundError(f"The folder for json env {json_dir} does not exist.")

        json_file_path = os.path.join(json_dir, cls.PLUGIN_ENVIRONMENT_JSON)

        # Write the dictionary to the JSON file
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(dict_, json_file, indent=4)

    @classmethod
    def setup_custom_directory(cls, source_path: str, destination_path: str):
        # Remove existing custom directory if it exists
        if os.path.exists(destination_path):
            print(f"Removing existing directory: {destination_path}")
            shutil.rmtree(destination_path)

        # Copy browser directory to custom directory
        print(f"Moving {source_path} to {destination_path}")
        shutil.move(source_path, destination_path)

        print(f"Successfully moved to {destination_path}")

    @classmethod
    def replace_relative_path(cls, original_path: str, prefix: str) -> str:
        """
        Replace relative paths with a prefixed path.
        """
        if original_path.startswith(('http://', 'https://', 'mailto:', '#', './static/custom')):
            return original_path
        if original_path.startswith('./'):
            return prefix + original_path[1:]
        return prefix + '/' + original_path

    @classmethod
    def modifiy_streamlit_index_html(cls):

        # Read the HTML files
        with open(cls.get_plugin_html_file_path(), 'r', encoding='utf-8') as file:
            source_html = file.read()

        with open(cls.get_streamlit_html_file_path(), 'r', encoding='utf-8') as file:
            destination_html = file.read()

        # Parse the HTML files with BeautifulSoup
        source_soup = BeautifulSoup(source_html, 'html.parser')
        destination_soup = BeautifulSoup(destination_html, 'html.parser')

        # 1. Copy styles from source to destination
        source_styles = source_soup.find_all('style')
        source_link_styles = source_soup.find_all('link', {'rel': 'stylesheet'})

        # Add version comment to the head of destination_soup
        cls._add_version_comment(destination_soup)
        # Add styles to the head of destination_soup
        cls._add_styles_to_head(source_styles, destination_soup)
        cls._add_link_styles_to_head(source_link_styles, destination_soup)

        # 2. Copy body content from source to destination
        if source_soup.body:
            cls._add_body_content(source_soup, destination_soup)

        cls._write_streamlit_html_file(destination_soup)

    @classmethod
    def reset_streamlit_index_html_file(cls) -> None:
        Logger.info("Resetting streamlit index.html file")

        with open(cls.get_streamlit_html_file_path(), 'r', encoding='utf-8') as file:
            streamlit_index_content = file.read()
        streamlit_index = BeautifulSoup(streamlit_index_content, 'html.parser')

        # Remove existing auto-added content from head
        cls._remove_existing_content(streamlit_index.head, cls.START_COMMENT, cls.END_COMMENT)
        # Remove existing version comment from head
        cls._remove_existing_content(streamlit_index.head, cls.VERSION_COMMENT, cls.VERSION_COMMENT)

        # Remove existing auto-added content from body
        cls._remove_existing_content(streamlit_index.body, cls.START_COMMENT, cls.END_COMMENT)

        # Write the modified HTML back to the destination file
        cls._write_streamlit_html_file(streamlit_index)

    @classmethod
    def _remove_existing_content(cls, container: BeautifulSoup, start_comment: str, end_comment: str):
        start_comments = container.find_all(
            string=lambda text: isinstance(text, Comment) and start_comment in text)
        for start_comment in start_comments:
            current = start_comment
            elements_to_remove = []

            # Collect all elements between start and end comments
            while current is not None:
                if isinstance(current, Comment) and end_comment in current:
                    elements_to_remove.append(current)
                    break
                elements_to_remove.append(current)
                current = current.next_element

            # Remove the collected elements
            for element in elements_to_remove:
                element.extract()

    @classmethod
    def _write_streamlit_html_file(cls, destination_soup: BeautifulSoup):
        index_path = cls.get_streamlit_html_file_path()
        with open(index_path, 'w', encoding='utf-8') as file:
            file.write(str(destination_soup.prettify()))

    @classmethod
    def _add_styles_to_head(cls, source_styles, destination_soup: BeautifulSoup):
        for style in source_styles:
            # Process the content to add ./static/custom to url() references
            if style.string:
                # Regular expression to find url() patterns with relative paths
                url_pattern = re.compile(r'url\([\'"]?(?!https?://|data:|\/\/|\.\/static\/custom)([^\'")]+)[\'"]?\)')
                style_text = style.string
                # Replace relative paths with prefixed paths
                style_text = url_pattern.sub(f'url({cls.get_plugin_relative_path()}/\\1)', style_text)
                style.string = style_text

            # Add comment before the style to mark it as added
            comment = Comment(cls.START_COMMENT)
            destination_soup.head.append(comment)
            destination_soup.head.append(style)
            comment = Comment(cls.END_COMMENT)
            destination_soup.head.append(comment)

    @classmethod
    def _add_link_styles_to_head(cls, source_link_styles, destination_soup: BeautifulSoup):
        for link in source_link_styles:
            # Skip if it's within a noscript tag
            if link.parent.name == 'noscript':
                continue

            # Modify relative paths in href
            if link.has_attr('href'):
                link['href'] = cls.replace_relative_path(link['href'], cls.get_plugin_relative_path())

            # Add comment before the link to mark it as added
            comment = Comment(cls.START_COMMENT)
            destination_soup.head.append(comment)
            destination_soup.head.append(link)
            comment = Comment(cls.END_COMMENT)
            destination_soup.head.append(comment)

    @classmethod
    def _add_version_comment(cls, destination_soup: BeautifulSoup):
        """
        Add a version comment to the head of the destination soup.
        """
        version_comment = Comment(f"{cls.VERSION_COMMENT}{cls.PLUGIN_VERSION}{cls.VERSION_COMMENT}")
        destination_soup.head.append(version_comment)

    @classmethod
    def _add_body_content(cls, source_soup, destination_soup):
        # Remove noscript tags from body content we'll copy
        for noscript in source_soup.body.find_all('noscript'):
            noscript.decompose()

        # Process all href attributes in the source body before copying
        for element in source_soup.body.find_all(href=True):
            element['href'] = cls.replace_relative_path(element['href'], cls.get_plugin_relative_path())

        # Process all src attributes in the source body before copying
        for element in source_soup.body.find_all(src=True):
            element['src'] = cls.replace_relative_path(element['src'], cls.get_plugin_relative_path())

        # Add a comment before appending content to clearly mark what's been added
        comment = Comment(cls.START_COMMENT)
        destination_soup.body.append(comment)

        # Append all children from the processed source body
        for element in list(source_soup.body.children):
            # Skip empty or whitespace-only text nodes
            if element.name is None and not element.strip():
                continue

            destination_soup.body.append(element)

        # Add a closing comment
        comment = Comment(cls.END_COMMENT)
        destination_soup.body.append(comment)

    @classmethod
    def clear_plugin(cls):
        """
        Clear the plugin by removing the custom directory.
        """
        # clear the index.html file
        cls.reset_streamlit_index_html_file()

        plugin_path = cls.get_plugin_path()
        if os.path.exists(plugin_path):
            shutil.rmtree(plugin_path)
