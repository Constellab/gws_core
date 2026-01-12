import importlib
import os
import traceback
from time import time
from typing import Any

from gws_core.brick.brick_dto import BrickDirectoryDTO, BrickInfo, BrickMessageStatus
from gws_core.brick.brick_model import BrickModel
from gws_core.brick.brick_settings import BrickSettings
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.settings import Settings
from gws_core.model.typing import Typing

from ..core.utils.logger import Logger
from ..core.utils.utils import Utils
from ..lab.system_status import SystemStatus
from .brick_helper import BrickHelper


class WaitingMessage(BaseModelDTO):
    brick_name: str
    message: str
    status: BrickMessageStatus
    timestamp: float


class BrickService:
    SOURCE_FOLDER = "src"

    _waiting_messages: list[WaitingMessage] = []

    @classmethod
    def log_brick_error(cls, obj: Any, message: str) -> None:
        cls.log_brick_message_from_obj(obj, message, "ERROR")

    @classmethod
    def log_brick_critical(cls, obj: Any, message: str) -> None:
        cls.log_brick_message_from_obj(obj, message, "CRITICAL")

    @classmethod
    def log_brick_info(cls, obj: Any, message: str) -> None:
        cls.log_brick_message_from_obj(obj, message, "INFO")

    @classmethod
    def log_brick_warning(cls, obj: Any, message: str) -> None:
        cls.log_brick_message_from_obj(obj, message, "WARNING")

    @classmethod
    def log_brick_message_from_obj(cls, obj: Any, message: str, status: BrickMessageStatus) -> None:
        """Log a message for the brick of the object. The message is save in DB so it can be viewed later

        :param obj: obj that caused the message. The brick information will be retrieve form the obj type
        :type obj: Any
        :param message: [description]
        :type message: str
        :param status: [description]
        :type status: BrickMessageStatus
        """
        brick_name: str
        try:
            brick_name = BrickHelper.get_brick_name(obj)
        except:
            brick_name = "__Unknown"

        cls.log_brick_message(brick_name=brick_name, message=message, status=status)

    @classmethod
    def log_brick_message(cls, brick_name: str, message: str, status: BrickMessageStatus) -> None:
        brick_message: WaitingMessage = WaitingMessage(
            brick_name=brick_name, message=message, status=status, timestamp=time()
        )

        if SystemStatus.app_is_initialized:
            cls._log_brick_message(brick_message)
        else:
            # Wait for the app to be initialized before saving the message
            cls._waiting_messages.append(brick_message)

    @classmethod
    def _log_brick_message(cls, brick_message: WaitingMessage) -> None:
        cls._log_message(brick_message)

        brick_model: BrickModel = cls._get_brick_model(brick_message.brick_name)

        if not brick_model:
            Logger.error(
                f"Can't log brick message because brick '{brick_message.brick_name}' was not found"
            )
            return
        brick_model.add_message(
            brick_message.message, brick_message.status, brick_message.timestamp
        )
        brick_model.save()

    @classmethod
    def _log_message(cls, brick_message: WaitingMessage) -> None:
        message = f"Brick '{brick_message.brick_name}'. {brick_message.message}'"
        if brick_message.status == "INFO":
            Logger.info(message)
        elif brick_message.status == "WARNING":
            Logger.warning(message)
        else:
            Logger.error(message)

    @classmethod
    def init(cls) -> None:
        """Clear the BrickModel table and log all the messages that were waiting on start"""
        BrickModel.clear_all_message()
        bricks_info: dict[str, BrickInfo] = BrickHelper.get_all_bricks()
        for brick_info in bricks_info.values():
            cls._init_brick_model(brick_info)

        for brick_message in cls._waiting_messages:
            cls._log_brick_message(brick_message)

        cls._waiting_messages = []

    @classmethod
    def _init_brick_model(cls, brick_info: BrickInfo) -> BrickModel:
        brick_model: BrickModel = cls._get_brick_model(brick_info.name)

        if brick_model is None:
            brick_model = BrickModel()
            brick_model.name = brick_info.name

        brick_model.status = "SUCCESS"
        brick_model.clear_messages()
        return brick_model.save()

    @classmethod
    def _get_brick_model(cls, brick_name: str) -> BrickModel:
        return BrickModel.find_by_name(brick_name)

    @classmethod
    def get_all_brick_models(cls) -> list[BrickModel]:
        return list(BrickModel.select().order_by(BrickModel.name))

    @classmethod
    def get_brick_model(cls, name: str) -> BrickModel:
        return BrickModel.find_by_name(name)

    @classmethod
    def get_brick_version(cls, name: str) -> str:
        brick = cls.get_brick_model(name)
        if not brick:
            raise BadRequestException(f"Brick {name} not found")
        return brick.get_version()

    @classmethod
    def list_brick_directories(cls, distinct: bool = False) -> list[BrickDirectoryDTO]:
        """List all brick directories from both user and system brick folders.

        Returns a list of BrickDirectoryDTO containing brick name and path.
        Only returns folders that are valid bricks (contain settings.json and src folder).

        :param distinct: If True, returns only one entry per brick name.
                        User folder bricks take priority over system folder bricks.
        :type distinct: bool
        :return: List of brick directories
        :rtype: List[BrickDirectoryDTO]
        """
        brick_directories: list[BrickDirectoryDTO] = []
        seen_brick_names = set()

        # Get both user and system brick folders
        user_bricks_folder = Settings.get_user_bricks_folder()
        sys_bricks_folder = Settings.get_sys_bricks_folder()

        # Check user bricks folder first (priority)
        if os.path.exists(user_bricks_folder) and os.path.isdir(user_bricks_folder):
            for item in os.listdir(user_bricks_folder):
                item_path = os.path.join(user_bricks_folder, item)
                if os.path.isdir(item_path) and cls.folder_is_brick(item_path):
                    brick_directories.append(
                        BrickDirectoryDTO(name=item, path=item_path, folder="user")
                    )
                    if distinct:
                        seen_brick_names.add(item)

        # Check system bricks folder
        if os.path.exists(sys_bricks_folder) and os.path.isdir(sys_bricks_folder):
            for item in os.listdir(sys_bricks_folder):
                item_path = os.path.join(sys_bricks_folder, item)
                if os.path.isdir(item_path) and cls.folder_is_brick(item_path):
                    # If distinct mode, skip bricks already seen in user folder
                    if distinct and item in seen_brick_names:
                        continue
                    brick_directories.append(
                        BrickDirectoryDTO(name=item, path=item_path, folder="system")
                    )

        # Sort by name for consistent ordering
        brick_directories.sort(key=lambda x: x.name)

        return brick_directories

    @classmethod
    def read_brick_settings(cls, brick_path: str) -> BrickSettings | None:
        """Read and parse the settings.json file from a brick folder path.

        :param brick_path: Path to the brick folder
        :type brick_path: str
        :return: BrickSettingsDTO with all settings, or None if file doesn't exist or can't be parsed
        :rtype: Optional[BrickSettingsDTO]
        """
        settings_file_path = os.path.join(brick_path, BrickSettings.FILE_NAME)
        return BrickSettings.from_file_path(settings_file_path)

    @classmethod
    def import_all_bricks_in_python(cls) -> None:
        bricks_info: dict[str, BrickInfo] = BrickHelper.get_all_bricks()
        for brick_name, brick_info in bricks_info.items():
            # for brick with error, just log the error and skip brick
            if brick_info.error:
                cls.log_brick_message(
                    brick_name=brick_name, message=brick_info.error, status="CRITICAL"
                )
                continue

            cls.import_brick_in_python(brick_name, brick_info.path)

    @classmethod
    def import_brick_in_python(cls, brick_name: str, brick_path: str) -> None:
        """Method to load a brick from path in python.

        :param brick_name: _description_
        :type brick_name: str
        :param brick_path: _description_
        :type brick_path: str
        """

        start_time = time()
        _, files = Utils.walk_dir(os.path.join(brick_path, cls.SOURCE_FOLDER))

        # loop through each file in the brick source folder
        for py_file in files:
            parts = py_file.split(f"/{cls.SOURCE_FOLDER}/")[-1].split("/")
            parts[-1] = os.path.splitext(parts[-1])[0]  # remove .py extension
            module_name = ".".join(parts)
            try:
                importlib.import_module(module_name)
            # On module load error, log an error but don't stop the app so a brick won't break the whole app
            except Exception as err:
                cls.log_brick_message(
                    brick_name=brick_name,
                    message=f"Cannot import module {module_name}. Skipping brick load. Error: {err}",
                    status="CRITICAL",
                )
                traceback.print_exc()
                # stop the brick load and go to next brick
                break

        cls.log_brick_message(
            brick_name=brick_name,
            message=f"Brick loaded in {round(time() - start_time, 2)}s",
            status="INFO",
        )

    @classmethod
    def folder_is_brick(cls, path: str) -> bool:
        """return true if the provided folder is a brick.
        If the folder contains a settings.json and a src folder it is a brick
        """
        return os.path.exists(os.path.join(path, BrickSettings.FILE_NAME)) and os.path.exists(
            os.path.join(path, cls.SOURCE_FOLDER)
        )

    @classmethod
    def get_parent_brick_folder(cls, path: str) -> str | None:
        """Get the parent brick folder of a file or folder path

        :param path: path to a file or folder
        :type path: str
        :return: the path to the parent brick folder, None if no parent brick folder was found
        :rtype: str
        """
        while path != "/":
            if cls.folder_is_brick(path):
                return path
            path = os.path.dirname(path)
        return None

    @classmethod
    def get_brick_name_from_path(cls, path: str) -> str | None:
        """Get the brick name from a folder path

        :param path: path to a file or folder inside a brick
        :type path: str
        :return: the brick name, None if the path is not inside a brick
        :rtype: str | None
        """
        brick_folder = cls.get_parent_brick_folder(path)
        if brick_folder:
            return os.path.basename(brick_folder)
        return None

    @classmethod
    def get_brick_src_folder(cls, brick_name: str) -> str:
        """Get the folder of the brick source code"""
        spec = importlib.util.find_spec(brick_name)

        if spec is not None:
            return os.path.dirname(spec.origin)
        else:
            raise Exception(f"Cannot find brick {brick_name}")

    @classmethod
    def find_brick_folder(cls, brick_name: str) -> str:
        """Find the folder of the brick by searching in the user bricks folder and the system bricks folder"""
        user_bricks_folder = Settings.get_user_bricks_folder()
        sys_bricks_folder = Settings.get_sys_bricks_folder()

        brick_path: str

        if os.path.exists(os.path.join(user_bricks_folder, brick_name)):
            brick_path = os.path.join(user_bricks_folder, brick_name)
        elif os.path.exists(os.path.join(sys_bricks_folder, brick_name)):
            brick_path = os.path.join(sys_bricks_folder, brick_name)
        else:
            raise Exception(
                f"Cannot find brick {brick_name} in bricks folder : '{user_bricks_folder}' or '{sys_bricks_folder}'"
            )

        if not cls.folder_is_brick(brick_path):
            raise Exception(
                f"The folder '{brick_path}' found for brick '{brick_name}' is not a brick"
            )

        return brick_path

    @classmethod
    def rename_brick(cls, old_brick_name: str, new_brick_name: str):
        r"""Rename brick objects and delete brick from settings
        /!\ This method is not safe and should be used with caution"""

        BrickModel.delete().where(BrickModel.name == old_brick_name).execute()

        Typing.delete().where(Typing.brick == old_brick_name).execute()

        Typing.get_db().execute_sql(
            f"UPDATE gws_resource SET resource_typing_name = REPLACE(resource_typing_name, '.{old_brick_name}.', '.{new_brick_name}.')"
        )
        Typing.get_db().execute_sql(
            f"UPDATE gws_task SET data = REPLACE(data, '.{old_brick_name}.', '.{new_brick_name}.')"
        )
        Typing.get_db().execute_sql(
            f"UPDATE gws_scenario_template SET data = REPLACE(data, '.{old_brick_name}.', '.{new_brick_name}.')"
        )

        Typing.get_db().execute_sql(
            f"UPDATE gws_task SET process_typing_name = REPLACE(process_typing_name, '.{old_brick_name}.', '.{new_brick_name}.')"
        )
        Typing.get_db().execute_sql(
            f"UPDATE gws_protocol SET process_typing_name = REPLACE(process_typing_name, '.{old_brick_name}.', '.{new_brick_name}.')"
        )

        Typing.get_db().execute_sql(
            f"UPDATE gws_scenario_template SET data = REPLACE(data, '.{old_brick_name}.', '.{new_brick_name}.')"
        )

    ################################ EXTENSIONS ################################

    @classmethod
    def get_brick_extensions_base_dir(cls, brick_name: str) -> str:
        """
        Get the extensions directory for a specific brick.
        You can store data of the brick in this folder.
        This folder is backup during backup process.

        :param brick_name: The name of the brick
        :type brick_name: `str`
        :return: The extensions directory for the brick
        :rtype: `str`
        """
        settings = Settings.get_instance()
        extensions_dir = settings.get_data_extensions_dir()
        return os.path.join(extensions_dir, brick_name)

    @classmethod
    def get_brick_extension_dir(cls, brick_name: str, extension_name: str) -> str:
        """
        Get the directory for a specific extension of a specific brick.
        You can store data of the brick in this folder.
        This folder is backup during backup process.

        Warnings: The docker service creates a directory in the extension folder
        with the unique_name of the compose service.
        So don't create a folder with the same name.

        :param brick_name: The name of the brick
        :type brick_name: `str`
        :param extension_name: The name of the extension
        :type extension_name: `str`
        :return: The directory for the extension of the brick
        :rtype: `str`
        """

        brick_extensions_dir = cls.get_brick_extensions_base_dir(brick_name)
        return os.path.join(brick_extensions_dir, extension_name)
