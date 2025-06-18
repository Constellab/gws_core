
from gws_core.apps.app_instance import AppInstance


class ReflexApp(AppInstance):
    """Object representing a Reflex app instance.
    This app instance is used to generate the app code and configuration files.

    :param AppInstance: _description_
    :type AppInstance: _type_
    :return: _description_
    :rtype: _type_
    """

    _app_folder: str = None

    MAIN_FILE_NAME = "rxconfig.py"

    def set_app_folder(self, app_folder_path: str) -> None:
        """Set the directory where the app will be generated"""
        self._app_folder = app_folder_path

    def get_app_folder(self) -> str:
        """Get the directory where the app will be generated"""
        return self._app_folder

    def generate_app(self, working_dir: str) -> None:
        if self._dev_mode:
            return

        app_config_dir = self._generate_config_dir(working_dir)

        self._generate_config(app_config_dir)

    def get_app_process_hash(self) -> str:
        # all are are using a different process
        return self.app_id
