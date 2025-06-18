

from typing import cast

from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_resource import AppResource
from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.impl.file.folder import Folder
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.resource.resource_decorator import resource_decorator


@resource_decorator("ReflexResource", human_name="Reflex app",
                    short_description="Reflex app")
class ReflexResource(AppResource):
    """
    Resource representing a Reflex app instance. https://reflex.dev/.

    This resource is used to generate the reflex app from the app config.

    The app can be configured in different ways:
    - By providing a Appconfig class annotated with @app_decorator.
    - By providing a folder path that contains the app code. The folder must contain a rxconfig.py file.

    This app supports the following features:
    - The app can be run in a virtual environment.
    - The app can be run with or without authentication.
    - The app can use resources as input.
    - The app can use parameters.

    /!\ Reflex cannot be installed in a normal Conda or Mamba environment.
    It must be installed using pip in a virtual environment.

    To use it in an conda virtual environment do the following:
    ```
    channels:
    - conda-forge
    dependencies:
    - pip
    - pip:
        - reflex
    ```

    :param AppResource: _description_
    :type AppResource: _type_
    """

    def get_main_app_file_name(self) -> str:
        """
        Get the name of the main app file. This is the file that will be executed when the app is started.

        :return: name of the main app file
        :rtype: str
        """
        return ReflexApp.MAIN_FILE_NAME

    def init_app_instance(self, shell_proxy: ShellProxy, app_id: str, app_name: str,
                          requires_authentification: bool = True) -> AppInstance:
        reflex_app = ReflexApp(app_id, app_name, shell_proxy,
                               requires_authentification)

        app_config = self._get_app_config()
        if app_config:
            folder_path = self._get_app_config_folder()
            reflex_app.set_app_folder(folder_path)
        elif self._code_folder_sub_resource_name is not None and len(self._code_folder_sub_resource_name) > 0:
            folder: Folder = cast(Folder, self.get_resource_by_name(self._code_folder_sub_resource_name))
            reflex_app.set_app_folder(folder.path)
        else:
            raise Exception("The app config or the code folder name must be set to generate the app.")

        return reflex_app
