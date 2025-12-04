import json
import os
import re

import streamlit
from bs4 import BeautifulSoup, Comment

from gws_core.apps.app_plugin_downloader import AppPluginDownloader
from gws_core.apps.app_plugin_html_parser import AppPluginHtmlParser
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings


class StreamlitPlugin(AppPluginDownloader):
    """Class to install the gws_plugin in the streamlit app.
    Extends ComponentPackageDownloader to add Streamlit-specific installation logic.

    The plugin is used to generate custom components in the streamlit app directly
    in the app without using the iframe.
    """

    # HTML comment used to identify the start and end of injected code in index.html
    # This is used to remove previously injected code before adding new code
    START_COMMENT = "[GWS_AUTO_ADD_START]"
    END_COMMENT = "[GWS_AUTO_ADD_END]"
    # This is used to identify the plugin version in the index.html file
    VERSION_COMMENT = "[GWS_PLUGIN_VERSION]"

    # Path of the index.html folder in the streamlit package
    INDEX_HTML_FOLDER = "static"
    INDEX_HTML = "index.html"
    INDEX_HTML_STATIC_FOLDER = "static"

    # Path of the injected code relative to index.html
    PLUGIN_FOLDER_NAME = "gws_plugin"
    PLUGIN_ENVIRONMENT_FOLDER = "assets"
    PLUGIN_ENVIRONMENT_JSON = "environment.json"
    PLUGIN_VERSION_FILE = "version.json"

    def __init__(self):
        """Initialize the StreamlitPlugin.
        Sets the package name to streamlit-components and destination folder to Streamlit's static folder.
        """
        streamlit_static_folder = os.path.join(self.get_plugin_path())
        super().__init__(
            package_name=self.STREAMLIT_COMPONENTS,
            destination_folder=streamlit_static_folder,
        )

    def get_streamlit_path(self) -> str:
        """
        Get the path to the streamlit package.
        """
        return os.path.dirname(streamlit.__file__)

    def post_install(self) -> None:
        """Override post_install to add Streamlit-specific installation logic.
        Modifies streamlit index.html and creates environment file after package download.
        """
        # Add Streamlit-specific installation steps
        self.modifiy_streamlit_index_html()
        self.create_environment_json_file()

    def post_uninstall(self) -> None:
        """Override post_uninstall to add Streamlit-specific cleanup logic.
        Resets the streamlit index.html file and then removes the package folder.
        """
        # Clear the streamlit index.html file
        self.reset_streamlit_index_html_file()

    def get_plugin_path(self) -> str:
        """
        Get the path to the plugin folder.
        """
        return os.path.join(self.get_streamlit_html_folder_path(), self.get_plugin_relative_path())

    def get_streamlit_html_folder_path(self) -> str:
        return os.path.join(self.get_streamlit_path(), self.INDEX_HTML_FOLDER)

    def get_streamlit_html_file_path(self) -> str:
        """
        Get the path to the streamlit HTML folder.
        """
        return os.path.join(self.get_streamlit_html_folder_path(), self.INDEX_HTML)

    def get_plugin_html_file_path(self) -> str:
        """
        Get the path to the plugin HTML folder.
        """
        return os.path.join(self.get_plugin_path(), self.INDEX_HTML)

    def get_plugin_relative_path(self) -> str:
        """
        Get the relative path to the plugin folder from stramlit index.html.
        """
        return os.path.join(self.INDEX_HTML_STATIC_FOLDER, self.PLUGIN_FOLDER_NAME)

    def get_installed_version(self) -> str | None:
        """To get the version we check the version in the index.html file and the version in the plugin folder.
        If both versions are present and match, we return the plugin version.
        If the versions do not match, we clear the plugin and return None. It is possible when
        the streamlit package is updated, the index.html file is updated but the plugin is not.
        If no version is found, we return None.

        :return: _description_
        :rtype: str | None
        """
        plugin_js_version = super().get_installed_version()

        if not plugin_js_version:
            return None

        index_version = self.get_version_from_index_html()
        if index_version != plugin_js_version:
            Logger.warning(
                f"Version mismatch: index.html version '{index_version}' "
                f"does not match installed plugin version '{plugin_js_version}'. "
                f"Using index.html version."
            )
            return None

        return plugin_js_version

    def get_version_from_index_html(self) -> str | None:
        """
        Get the version of the plugin from the index.html file.
        Extract the text between the version comment tags.
        """
        index_html_path = self.get_streamlit_html_file_path()
        if not os.path.exists(index_html_path):
            return None

        with open(index_html_path, "r", encoding="utf-8") as file:
            content = file.read()
            # Use regex to find the version comment
            version_pattern = re.compile(
                r"<!--\s*"
                + re.escape(self.VERSION_COMMENT)
                + r"(\S+)\s*"
                + re.escape(self.VERSION_COMMENT)
                + r"-->"
            )
            match = version_pattern.search(content)
            if match:
                return match.group(1)

    def create_environment_json_file(self):
        """Create the environment.json file for the plugin."""
        dict_ = {
            "apiBaseUrl": Settings.get_lab_api_url(),
            "baseHref": self.get_plugin_relative_path(),
            "spaceApiUrl": Settings.get_space_api_url(),
            "communityFrontUrl": Settings.get_community_front_url(),
            "communityApiUrl": Settings.get_community_api_url(),
        }

        # Define the path for the JSON file
        json_dir = os.path.join(self.get_plugin_path(), self.PLUGIN_ENVIRONMENT_FOLDER)
        # if the file doesn't exists, throw an error
        if not os.path.exists(json_dir):
            raise FileNotFoundError(f"The folder for json env {json_dir} does not exist.")

        json_file_path = os.path.join(json_dir, self.PLUGIN_ENVIRONMENT_JSON)

        # Write the dictionary to the JSON file
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(dict_, json_file, indent=4)

    def modifiy_streamlit_index_html(self):
        """Modify the Streamlit index.html file to inject the plugin."""
        # Read the HTML files
        with open(self.get_plugin_html_file_path(), "r", encoding="utf-8") as file:
            source_html = file.read()

        with open(self.get_streamlit_html_file_path(), "r", encoding="utf-8") as file:
            destination_html = file.read()

        # Parse source HTML using HtmlParser
        html_parser = AppPluginHtmlParser(relative_path_prefix=self.get_plugin_relative_path())
        parsed_html = html_parser.parse(source_html)

        # Parse destination HTML with BeautifulSoup
        destination_soup = BeautifulSoup(destination_html, "html.parser")

        # Add version comment to the head of destination_soup
        self._add_version_comment(destination_soup)

        # Add styles to the head of destination_soup
        self._add_parsed_styles_to_head(parsed_html.head_styles, destination_soup)

        # Add body content from parsed HTML (this now includes links, scripts, and HTML content)
        self._add_parsed_body_to_destination(parsed_html.body, destination_soup)

        self._write_streamlit_html_file(destination_soup)

    def reset_streamlit_index_html_file(self) -> None:
        """Reset the Streamlit index.html file by removing plugin-related content."""
        Logger.info("Resetting streamlit index.html file")

        with open(self.get_streamlit_html_file_path(), "r", encoding="utf-8") as file:
            streamlit_index_content = file.read()
        streamlit_index = BeautifulSoup(streamlit_index_content, "html.parser")

        # Remove existing auto-added content from head
        self._remove_existing_content(streamlit_index.head, self.START_COMMENT, self.END_COMMENT)
        # Remove existing version comment from head
        self._remove_existing_content(
            streamlit_index.head, self.VERSION_COMMENT, self.VERSION_COMMENT
        )

        # Remove existing auto-added content from body
        self._remove_existing_content(streamlit_index.body, self.START_COMMENT, self.END_COMMENT)

        # Write the modified HTML back to the destination file
        self._write_streamlit_html_file(streamlit_index)

    def _remove_existing_content(
        self, container: BeautifulSoup, start_comment: str, end_comment: str
    ):
        start_comments = container.find_all(
            string=lambda text: isinstance(text, Comment) and start_comment in text
        )
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

    def _write_streamlit_html_file(self, destination_soup: BeautifulSoup):
        index_path = self.get_streamlit_html_file_path()
        with open(index_path, "w", encoding="utf-8") as file:
            file.write(str(destination_soup.prettify()))

    def _add_parsed_styles_to_head(self, styles, destination_soup: BeautifulSoup):
        """Add parsed styles to the destination head.
        Note: The parser now only returns external stylesheets (no inline styles).
        """
        for style_obj in styles:
            # Add start comment
            comment = Comment(self.START_COMMENT)
            destination_soup.head.append(comment)

            # Create <link> tag for external stylesheet
            link_tag = destination_soup.new_tag("link", rel="stylesheet")
            link_tag["href"] = style_obj.href

            # Add any additional attributes
            for attr_name, attr_value in style_obj.attributes.items():
                link_tag[attr_name] = attr_value

            destination_soup.head.append(link_tag)

            # Add end comment
            comment = Comment(self.END_COMMENT)
            destination_soup.head.append(comment)

    def _add_version_comment(self, destination_soup: BeautifulSoup):
        """
        Add a version comment to the head of the destination soup.
        """
        version_comment = Comment(
            f"{self.VERSION_COMMENT}{self.DASHBOARD_COMPONENTS_VERSION}{self.VERSION_COMMENT}"
        )
        destination_soup.head.append(version_comment)

    def _add_parsed_body_to_destination(self, body_obj, destination_soup: BeautifulSoup):
        """Add parsed body content (HTML, links, and scripts) to the destination body.
        Note: The parser now only returns external scripts (no inline scripts).
        """
        # Add start comment
        comment = Comment(self.START_COMMENT)
        destination_soup.body.append(comment)

        # 1. Add HTML content first
        if body_obj.content:
            body_content_soup = BeautifulSoup(body_obj.content, "html.parser")
            for element in body_content_soup.children:
                # Skip empty or whitespace-only text nodes
                if hasattr(element, "name") and element.name is None and not str(element).strip():
                    continue
                destination_soup.body.append(element)

        # 2. Add links (modulepreload, etc.)
        for link_obj in body_obj.links:
            link_tag = destination_soup.new_tag("link")
            link_tag["href"] = link_obj.href
            link_tag["rel"] = link_obj.rel

            # Add any additional attributes
            for attr_name, attr_value in link_obj.attributes.items():
                link_tag[attr_name] = attr_value

            destination_soup.body.append(link_tag)

        # 3. Add external scripts
        for script_obj in body_obj.scripts:
            # Create <script> tag with src
            script_tag = destination_soup.new_tag("script")
            script_tag["src"] = script_obj.src

            # Add any additional attributes
            for attr_name, attr_value in script_obj.attributes.items():
                script_tag[attr_name] = attr_value

            destination_soup.body.append(script_tag)

        # Add end comment
        comment = Comment(self.END_COMMENT)
        destination_soup.body.append(comment)
