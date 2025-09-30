

import importlib
import os
import traceback
from time import time
from typing import Any, Dict, List, Optional

from gws_core.brick.brick_dto import BrickInfo, BrickMessageStatus
from gws_core.brick.brick_model import BrickModel
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
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


class BrickService():

    SETTINGS_JSON_FILE = "settings.json"
    SOURCE_FOLDER = "src"

    _waiting_messages: List[WaitingMessage] = []

    @classmethod
    def log_brick_error(cls, obj: Any, message: str) -> None:
        cls.log_brick_message_from_obj(obj, message, 'ERROR')

    @classmethod
    def log_brick_critical(cls, obj: Any, message: str) -> None:
        cls.log_brick_message_from_obj(obj, message, 'CRITICAL')

    @classmethod
    def log_brick_info(cls, obj: Any, message: str) -> None:
        cls.log_brick_message_from_obj(obj, message, 'INFO')

    @classmethod
    def log_brick_warning(cls, obj: Any, message: str) -> None:
        cls.log_brick_message_from_obj(obj, message, 'WARNING')

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
            brick_name = '__Unknown'

        cls.log_brick_message(brick_name=brick_name,
                              message=message, status=status)

    @classmethod
    def log_brick_message(cls, brick_name: str, message: str, status: BrickMessageStatus) -> None:
        brick_message: WaitingMessage = WaitingMessage(brick_name=brick_name,
                                                       message=message, status=status, timestamp=time())

        if SystemStatus.app_is_initialized:
            cls._log_brick_message(brick_message)
        else:
            # Wait for the app to be initialized before saving the message
            cls._waiting_messages.append(brick_message)

    @classmethod
    def _log_brick_message(cls, brick_message: WaitingMessage) -> None:
        cls._log_message(brick_message)

        brick_model: BrickModel = cls._get_brick_model(
            brick_message.brick_name)

        if not brick_model:
            Logger.error(
                f"Can't log brick message because brick '{brick_message.brick_name}' was not found")
            return
        brick_model.add_message(
            brick_message.message, brick_message.status, brick_message.timestamp)
        brick_model.save()

    @classmethod
    def _log_message(cls, brick_message: WaitingMessage) -> None:
        message = f"Brick '{brick_message.brick_name}'. {brick_message.message}'"
        if brick_message.status == 'INFO':
            Logger.info(message)
        elif brick_message.status == 'WARNING':
            Logger.warning(message)
        else:
            Logger.error(message)

    @classmethod
    def init(cls) -> None:
        """Clear the BrickModel table and log all the messages that were waiting on start
        """
        BrickModel.clear_all_message()
        bricks_info: Dict[str, BrickInfo] = BrickHelper.get_all_bricks()
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

        brick_model.status = 'SUCCESS'
        brick_model.clear_messages()
        return brick_model.save()

    @classmethod
    def _get_brick_model(cls, brick_name: str) -> BrickModel:
        return BrickModel.find_by_name(brick_name)

    @classmethod
    def get_all_brick_models(cls) -> List[BrickModel]:
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
    def import_all_bricks_in_python(cls) -> None:
        bricks_info: Dict[str, BrickInfo] = BrickHelper.get_all_bricks()
        for brick_name, brick_info in bricks_info.items():

            # for brick with error, just log the error and skip brick
            if brick_info.error:
                cls.log_brick_message(brick_name=brick_name,
                                      message=brick_info.error,
                                      status='CRITICAL')
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
                    status='CRITICAL')
                traceback.print_exc()
                # stop the brick load and go to next brick
                break

        cls.log_brick_message(
            brick_name=brick_name,
            message=f"Brick loaded in {round(time() - start_time, 2)}s",
            status='INFO')

    @classmethod
    def folder_is_brick(cls, path: str) -> bool:
        """return true if the provided folder is a brick.
        If the folder contains a settings.json and a src folder it is a brick
        """
        return os.path.exists(os.path.join(path, cls.SETTINGS_JSON_FILE)) and \
            os.path.exists(os.path.join(path, cls.SOURCE_FOLDER))

    @classmethod
    def get_parent_brick_folder(cls, path: str) -> Optional[str]:
        """Get the parent brick folder of a file or folder path

        :param path: path to a file or folder
        :type path: str
        :return: the path to the parent brick folder, None if no parent brick folder was found
        :rtype: str
        """
        while path != '/':
            if cls.folder_is_brick(path):
                return path
            path = os.path.dirname(path)
        return None

    @classmethod
    def get_brick_src_folder(cls, brick_name: str) -> str:
        """Get the folder of the brick source code
        """
        spec = importlib.util.find_spec(brick_name)

        if spec is not None:
            return os.path.dirname(spec.origin)
        else:
            raise Exception(f"Cannot find brick {brick_name}")

    @classmethod
    def find_brick_folder(cls, brick_name: str) -> str:
        """Find the folder of the brick by searching in the user bricks folder and the system bricks folder
        """
        user_bricks_folder = Settings.get_user_bricks_folder()
        sys_bricks_folder = Settings.get_sys_bricks_folder()

        brick_path: str

        if os.path.exists(os.path.join(user_bricks_folder, brick_name)):
            brick_path = os.path.join(user_bricks_folder, brick_name)
        elif os.path.exists(os.path.join(sys_bricks_folder, brick_name)):
            brick_path = os.path.join(sys_bricks_folder, brick_name)
        else:
            raise Exception(
                f"Cannot find brick {brick_name} in bricks folder : '{user_bricks_folder}' or '{sys_bricks_folder}'")

        if not cls.folder_is_brick(brick_path):
            raise Exception(f"The folder '{brick_path}' found for brick '{brick_name}' is not a brick")

        return brick_path

    @classmethod
    def rename_brick(cls, old_brick_name: str, new_brick_name: str):
        """Rename brick objects and delete brick from settings
        /!\ This method is not safe and should be used with caution"""

        BrickModel.delete().where(BrickModel.name == old_brick_name).execute()

        Typing.delete().where(Typing.brick == old_brick_name).execute()

        Typing.get_db().execute_sql(
            f"UPDATE gws_resource SET resource_typing_name = REPLACE(resource_typing_name, '.{old_brick_name}.', '.{new_brick_name}.')")
        Typing.get_db().execute_sql(
            f"UPDATE gws_task SET data = REPLACE(data, '.{old_brick_name}.', '.{new_brick_name}.')")
        Typing.get_db().execute_sql(
            f"UPDATE gws_scenario_template SET data = REPLACE(data, '.{old_brick_name}.', '.{new_brick_name}.')")

        Typing.get_db().execute_sql(
            f"UPDATE gws_task SET process_typing_name = REPLACE(process_typing_name, '.{old_brick_name}.', '.{new_brick_name}.')")
        Typing.get_db().execute_sql(
            f"UPDATE gws_protocol SET process_typing_name = REPLACE(process_typing_name, '.{old_brick_name}.', '.{new_brick_name}.')")

        Typing.get_db().execute_sql(
            f"UPDATE gws_scenario_template SET data = REPLACE(data, '.{old_brick_name}.', '.{new_brick_name}.')")
