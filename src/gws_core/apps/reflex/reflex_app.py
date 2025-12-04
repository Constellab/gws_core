import os
from typing import Optional

from gws_core.apps.app_config import AppConfig
from gws_core.apps.app_dto import AppType
from gws_core.apps.app_instance import AppInstance
from gws_core.core.utils.logger import Logger
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigins
from gws_core.tag.tag_entity_type import TagEntityType


class ReflexApp(AppInstance):
    """Object representing a Reflex app instance.
    This app instance is used to generate the app code and configuration files.

    :param AppInstance: _description_
    :type AppInstance: _type_
    :return: _description_
    :rtype: _type_
    """

    # if a static folder is provided
    _app_static_folder: str = None

    # If app config is set,
    _app_config: AppConfig = None

    # The folder that contains the front build of the app.
    _front_app_build_folder: Folder = None

    _is_enterprise: bool = False

    MAIN_FILE_NAME = "rxconfig.py"

    # Keys of the tag set in the ReflexResource to store the version of front build.
    # The value is the current brick version.
    FRONT_BUILD_TAG_KEY_NAME = "reflex_build_brick_name"
    FRONT_BUILD_TAG_KEY_VERSION = "reflex_build_brick_version"

    INDEX_FILE_NAME = "index.html"

    CACHE_FOLDER_NAMES = [".states", ".web", os.path.join("assets", "external")]

    def set_app_config(self, app_config: AppConfig, front_app_build_folder: Folder) -> None:
        """Set the app config for this app instance.
        The app config is used to generate the app code and configuration files.

        :param app_config: _description_
        :type app_config: AppConfig
        """
        self._app_config = app_config
        self._front_app_build_folder = front_app_build_folder

    def get_front_app_build_folder(self) -> Optional[Folder]:
        """Get the folder that contains the front build of the app.
        This folder is created by the task that generates the app.

        :return: The folder that contains the front build of the app.
        :rtype: Optional[Folder]
        """
        return self._front_app_build_folder if self._front_app_build_folder else None

    def get_app_config(self) -> AppConfig:
        """Get the app config for this app instance.

        :return: _description_
        :rtype: AppConfig
        """
        return self._app_config

    def set_app_static_folder(self, app_folder_path: str, front_app_build_folder: Folder) -> None:
        """Set the directory where the app will be generated"""
        self._app_static_folder = app_folder_path
        self._front_app_build_folder = front_app_build_folder

    def get_app_folder(self) -> str:
        """Get the directory where the app will be generated"""
        if self._app_config:
            return self._app_config.get_app_folder_path()
        return self._app_static_folder

    def generate_app(self, working_dir: str) -> None:
        """Generate the dir for the process. Then inside this dir
        generate a dir for this app and generate the app configuration file.

        :param working_dir: _description_
        :type working_dir: str
        """
        app_config_dir = self._generate_config_dir(working_dir)

        if self._dev_mode:
            self._generate_config_dev_mode()
        else:
            self._generate_config(app_config_dir)

    def get_app_process_hash(self) -> str:
        # all app are using a different process
        return self.resource_model_id

    def get_app_type(self) -> AppType:
        """Get the type of the app."""
        return AppType.REFLEX

    def update_front_build_info(self) -> None:
        """Update the front build brick version.
        This is used to update the front build version after the app is generated.

        :param brick_version: The new brick version.
        :type brick_version: str
        """
        app_config = self.get_app_config()
        if not app_config:
            return

        Logger.info(
            f"Updating front build info for app {self.resource_model_id} with brick name {app_config.get_brick_name()} "
            + f"and version {app_config.get_brick_version()}"
        )

        resource_list = EntityTagList.find_by_entity(TagEntityType.RESOURCE, self.resource_model_id)

        resource_list.replace_tags(
            [
                # Tag containing the brick name of the front build
                Tag(
                    key=ReflexApp.FRONT_BUILD_TAG_KEY_NAME,
                    value=app_config.get_brick_name(),
                    origins=TagOrigins.system_origins(),
                ),
                # Tag containing the brick version of the front build
                Tag(
                    key=ReflexApp.FRONT_BUILD_TAG_KEY_VERSION,
                    value=str(app_config.get_brick_version()),
                    origins=TagOrigins.system_origins(),
                ),
            ]
        )

    def _get_front_built_brick_version(self) -> Optional[str]:
        """Get the front build brick version.
        This is used to check if the front build is up to date.

        :return: The front build brick version.
        :rtype: str
        """
        resource_list = EntityTagList.find_by_entity(TagEntityType.RESOURCE, self.resource_model_id)
        version_tag = resource_list.get_first_tag_by_key(ReflexApp.FRONT_BUILD_TAG_KEY_VERSION)
        if version_tag:
            return version_tag.tag_value
        return None

    def get_front_build_path_if_exists(self) -> Optional[str]:
        """Check if the front build is already generated.
        If the build was generated from a previous brick version, it will be deleted
        and considered as not built.

        :return: True if the front build is set, False otherwise.
        :rtype: bool
        """
        # if directory is not empty, skip build
        build_folder = self._front_app_build_folder
        if not build_folder:
            raise Exception(
                "The front build folder is not set. Please call `set_app_config` or `set_app_static_folder` before generating the app."
            )

        if not FileHelper.exists_on_os(build_folder.path):
            raise Exception(
                f"Front build folder {build_folder.path} does not exist. Please re-generate the app."
            )

        index_path = os.path.join(build_folder.path, ReflexApp.INDEX_FILE_NAME)
        if not FileHelper.exists_on_os(index_path):
            Logger.error(
                f"Front build folder {build_folder.path} does not contain the index file. Rebuilding frontend."
            )
            FileHelper.delete_dir_content(build_folder.path)
            return None

        app_config = self.get_app_config()

        if not app_config:
            # this is static folder mode, no need to check the version
            return build_folder.path

        # get the current brick version
        current_brick_version = app_config.get_brick_version()

        build_brick_version = self._get_front_built_brick_version()
        if current_brick_version.to_string() != build_brick_version:
            Logger.info(
                f"Frontend build version {build_brick_version} does not match current version {current_brick_version} for app {self.resource_model_id}. Cleaning old build."
            )
            build_folder.empty_folder()
            return None

        return build_folder.path

    def get_front_build_path_from_app(self, app_path: str) -> str:
        return os.path.join(app_path, ".web", "build", "client")

    def set_is_enterprise(self, is_enterprise: bool) -> None:
        self._is_enterprise = is_enterprise

    def is_enterprise(self) -> bool:
        return self._is_enterprise

    def clear_app_cache(self) -> None:
        """Clear the Reflex app cache by deleting specific folders.
        Deletes the following folders if they exist:
        - .states
        - .web
        - assets/external
        """
        app_src_folder_path = self._shell_proxy.working_dir
        if not FileHelper.exists_on_os(app_src_folder_path):
            return

        cache_folders = [
            os.path.join(app_src_folder_path, folder_name)
            for folder_name in self.CACHE_FOLDER_NAMES
        ]

        for folder_path in cache_folders:
            if FileHelper.exists_on_os(folder_path):
                try:
                    FileHelper.delete_dir(folder_path, ignore_errors=False)
                    Logger.info(f"Deleted cache folder: {folder_path}")
                except Exception as e:
                    Logger.error(f"Failed to delete cache folder {folder_path}: {str(e)}")
