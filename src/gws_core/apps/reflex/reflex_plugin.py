import os

from gws_core.apps.app_plugin_downloader import AppPluginDownloader


class ReflexPlugin(AppPluginDownloader):
    """Class to install the gws_plugin in the Reflex app.
    Extends AppPluginDownloader to add Reflex-specific installation logic.

    The plugin is used to generate custom components from gws library for Reflex apps.

    The package itself lives in the lab-wide immutable store (see AppPluginDownloader)
    and is materialized (copied) into the app's `assets/external/gws_plugin` folder.
    Several instances of the same app share that folder, so the copy is staged and
    swapped atomically by the base class.
    """

    GWS_PLUGIN_FOLDER_NAME = os.path.join("external", "gws_plugin")

    def __init__(self, app_folder: str | None = None):
        """Initialize the ReflexPlugin.

        :param app_folder: root folder of the Reflex app. Defaults to the current working
            directory (inside a running Reflex app the cwd is the app folder).
        :type app_folder: str, optional
        """
        self._app_folder = app_folder or os.getcwd()
        super().__init__(
            package_name=self.REFLEX_COMPONENTS,
            materialize_target=self._get_asset_plugin_folder_path(),
        )

    def pre_materialize_finalize(self, staging_folder: str) -> None:
        """Write the environment.json into the staging copy so the materialized folder
        is complete the instant it is swapped into place."""
        self.create_environment_json_file(staging_folder)

    def get_base_href(self) -> str:
        return self.GWS_PLUGIN_FOLDER_NAME

    def _get_reflex_assets_folder_path(self) -> str:
        """Get the path to the Reflex app's root assets folder.

        :return: Path to assets folder
        """
        return os.path.join(self._app_folder, self.ASSETS_FOLDER_NAME)

    def _get_asset_plugin_folder_path(self) -> str:
        """Get the path to the gws_plugin folder in the Reflex app's assets folder.

        :return: Path to gws_plugin folder
        """
        return os.path.join(self._get_reflex_assets_folder_path(), self.GWS_PLUGIN_FOLDER_NAME)
