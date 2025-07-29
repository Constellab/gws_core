

from typing import cast

from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_resource import AppResource
from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.impl.file.folder import Folder
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.resource.r_field.primitive_r_field import StrRField
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

    _front_build_sub_resource_uid: str = StrRField()

    def set_app_config(self, app_config):
        super().set_app_config(app_config)
        self._init_front_build_sub_resource()

    def set_static_folder(self, app_folder_path):
        super().set_static_folder(app_folder_path)
        self._init_front_build_sub_resource()

    def _init_front_build_sub_resource(self):
        """Init the reflex app resource. This must be called after creating the resource.


        :param brick_name: Name of the brick of the task that generated this app.
                            Use `self.get_brick_name()` to get the name of the current brick from task.
        :type brick_name: str
        """

        if self._front_build_sub_resource_uid:
            return

        folder = Folder.new_temp_folder()
        folder.name = 'App build folder'
        # create an empty folder sub resource to store the front build
        self.add_resource(folder, create_new_resource=True)
        self._front_build_sub_resource_uid = folder.uid

    def get_and_check_front_build_folder(self) -> Folder:
        """Get the folder that contains the front build of the app.
        This folder is created by the task that generates the app.

        :return: The folder that contains the front build of the app.
        :rtype: Folder
        """
        for resource in self.get_resources():
            if resource.uid == self._front_build_sub_resource_uid:
                if isinstance(resource, Folder):
                    return cast(Folder, resource)
                else:
                    raise Exception(
                        f"The front build sub resource {self._front_build_sub_resource_uid} is not a folder")
        raise Exception(
            f"The front build sub resource {self._front_build_sub_resource_uid} was not found in the resources of the app")

    def get_main_app_file_name(self) -> str:
        """
        Get the name of the main app file. This is the file that will be executed when the app is started.

        :return: name of the main app file
        :rtype: str
        """
        return ReflexApp.MAIN_FILE_NAME

    def init_app_instance(self, shell_proxy: ShellProxy, resource_model_id: str, app_name: str,
                          requires_authentification: bool = True) -> AppInstance:

        reflex_app = ReflexApp(resource_model_id, app_name, shell_proxy,
                               requires_authentification)

        front_build_folder = self.get_and_check_front_build_folder()
        app_config = self._get_app_config()
        if app_config:
            reflex_app.set_app_config(app_config, front_build_folder)
        elif self._code_folder_sub_resource_name is not None and len(self._code_folder_sub_resource_name) > 0:
            folder: Folder = cast(Folder, self.get_resource_by_name(self._code_folder_sub_resource_name))
            reflex_app.set_app_static_folder(folder.path, front_build_folder)
        else:
            raise Exception("The app config or the code folder name must be set to generate the app.")

        return reflex_app
