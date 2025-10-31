import os

from gws_core.apps.app_plugin_downloader import AppPluginDownloader
from gws_core.apps.app_plugin_html_parser import AppPluginHtmlParser
from gws_core.core.utils.logger import Logger


class ReflexPlugin(AppPluginDownloader):
    """Class to install the gws_plugin in the Reflex app.
    Extends AppPackageDownloader to add Reflex-specific installation logic.

    The plugin is used to generate custom components from gws library for Reflex apps.
    """

    ASSETS_FOLDER_NAME = "assets"
    GWS_PLUGIN_FOLDER_NAME = os.path.join("external", "gws_plugin")
    INDEX_HTML_FILE_NAME = "index.html"

    def __init__(self):
        """Initialize the ReflexComponent.
        Sets the package name to streamlit-components and destination folder to Reflex's asset folder.

        :param asset_path: Path to the asset folder
        """
        super().__init__(
            package_name=self.REFLEX_COMPONENTS,
            destination_folder=self._get_asset_plugin_folder_path(),
        )

    def post_install(self):
        """Override post_install to add Reflex-specific installation logic.
        Creates a main.js file that imports all JS files and CSS files referenced in the index.html.
        """
        # Auto-detect index.html path if not provided
        index_html_path = self._get_index_html_path()
        if not os.path.exists(index_html_path):
            raise Exception(f"Index.html file not found at {index_html_path}, skipping main.js creation")

        # Create main.js file with imports from index.html
        self._create_main_js()

    def _create_main_js(self):
        """Create a main.js file in the same directory as index.html.
        The main.js file will import all JS files, modulepreload links, and CSS files
        that are referenced in the index.html file using the HtmlParser.
        """
        # Read and parse the index.html file
        index_html_path = self._get_index_html_path()
        with open(index_html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Use HtmlParser to extract all components with './' prefix for relative imports
        # The parser now only returns relative (external) resources, filtering out inline content and absolute URLs
        parser = AppPluginHtmlParser(relative_path_prefix="./")
        parsed_html = parser.parse(html_content)

        # Collect all imports in order: modulepreload links, scripts, then CSS
        all_imports = []

        # Add modulepreload links from body
        for link in parsed_html.body.links:
            if link.rel == 'modulepreload':
                all_imports.append(link.href)

        # Add external scripts from body
        for script in parsed_html.body.scripts:
            all_imports.append(script.src)

        # Add CSS stylesheets from head
        for style in parsed_html.head_styles:
            all_imports.append(style.href)

        if not all_imports:
            Logger.warning("No JS or CSS imports found in index.html, skipping main.js creation")
            return

        # Create the main.js content with import statements
        main_js_content = "// Auto-generated file that imports all JS modules and CSS from index.html\n\n"
        for import_file in all_imports:
            main_js_content += f"import '{import_file}';\n"

        # Write the main.js file in the same directory as index.html
        index_html_dir = os.path.dirname(index_html_path)
        main_js_path = os.path.join(index_html_dir, 'main.js')

        with open(main_js_path, 'w', encoding='utf-8') as file:
            file.write(main_js_content)

        Logger.info(f"Created main.js file at {main_js_path} with {len(all_imports)} imports")

    def _get_assets_folder_path(self) -> str:
        """Get the path to the assets folder in the destination folder.

        :return: Path to assets folder
        """
        return os.path.join(os.getcwd(), self.ASSETS_FOLDER_NAME)

    def _get_asset_plugin_folder_path(self) -> str:
        """Get the path to the gws_plugin folder in the assets folder.

        :return: Path to gws_plugin folder
        """
        return os.path.join(self._get_assets_folder_path(), self.GWS_PLUGIN_FOLDER_NAME)

    def _get_index_html_path(self) -> str:
        """Get the path to the index.html file in the destination folder.

        :return: Path to index.html
        """
        return os.path.join(self._get_asset_plugin_folder_path(), self.INDEX_HTML_FILE_NAME)
