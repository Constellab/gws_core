import os

from gws_core.apps.app_plugin_downloader import AppPluginDownloader


class ReflexPlugin(AppPluginDownloader):
    """Class to install the gws_plugin in the Reflex app.
    Extends AppPackageDownloader to add Reflex-specific installation logic.

    The plugin is used to generate custom components from gws library for Reflex apps.
    """

    GWS_PLUGIN_FOLDER_NAME = os.path.join("external", "gws_plugin")

    def __init__(self):
        """Initialize the ReflexComponent.
        Sets the package name to streamlit-components and destination folder to Reflex's asset folder.

        :param asset_path: Path to the asset folder
        """
        super().__init__(
            package_name=self.REFLEX_COMPONENTS,
            destination_folder=self._get_asset_plugin_folder_path(),
        )

    def post_install(self) -> None:
        """Create the environment.json file after the plugin package is downloaded."""
        self.create_environment_json_file()

    def get_base_href(self) -> str:
        return self.GWS_PLUGIN_FOLDER_NAME

    def _get_reflex_assets_folder_path(self) -> str:
        """Get the path to the Reflex app's root assets folder.

        :return: Path to assets folder
        """
        return os.path.join(os.getcwd(), self.ASSETS_FOLDER_NAME)

    def _get_asset_plugin_folder_path(self) -> str:
        """Get the path to the gws_plugin folder in the Reflex app's assets folder.

        :return: Path to gws_plugin folder
        """
        return os.path.join(self._get_reflex_assets_folder_path(), self.GWS_PLUGIN_FOLDER_NAME)
