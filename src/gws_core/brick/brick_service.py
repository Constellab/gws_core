

import importlib
import os
import traceback
from time import time
from typing import Any, Dict, List, TypedDict

from ..core.utils.logger import Logger
from ..core.utils.settings import ModuleInfo
from ..core.utils.utils import Utils
from ..lab.system_status import SystemStatus
from .brick_helper import BrickHelper
from .brick_model import BrickMessageStatus, BrickModel


class WaitingMessage(TypedDict):
    brick_name: str
    brick_path: str
    message: str
    status: BrickMessageStatus
    timestamp: float


class BrickService():

    _waiting_messages: List[WaitingMessage] = []

    @classmethod
    def log_brick_error(cls, obj: Any, message: str) -> None:
        cls.log_brick_message_from_obj(obj, message, 'ERROR')

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
        brick_path: str
        try:
            brick_name = BrickHelper.get_brick_name(obj)
            brick_path = BrickHelper.get_brick_path(obj)
        except:
            brick_name = '__Unknown'
            brick_path = ''

        cls.log_brick_message(brick_name=brick_name, brick_path=brick_path, message=message, status=status)

    @classmethod
    def log_brick_message(cls, brick_name: str, brick_path: str, message: str, status: BrickMessageStatus) -> None:
        brick_message: WaitingMessage = {"brick_name": brick_name, "brick_path": brick_path,
                                         "message": message, "status": status, "timestamp": time()}

        if SystemStatus.app_is_initialized:
            cls._log_brick_message(brick_message)
        else:
            # Wait for the app to be initialized before saving the message
            cls._waiting_messages.append(brick_message)

    @classmethod
    def _log_brick_message(cls, brick_message: WaitingMessage) -> None:
        cls._log_message(brick_message)

        brick_model: BrickModel = cls._get_or_create_brick(brick_message['brick_name'], brick_message['brick_path'])
        brick_model.add_message(brick_message['message'], brick_message['status'], brick_message['timestamp'])
        brick_model.save()

    @classmethod
    def _log_message(cls, brick_message: WaitingMessage) -> None:
        message = f"Error in brick '{brick_message['brick_name']}. {brick_message['message']}'"
        if brick_message['status'] == 'INFO':
            Logger.info(message)
        elif brick_message['status'] == 'WARNING':
            Logger.warning(message)
        else:
            Logger.error(message)

    @classmethod
    def init(cls) -> None:
        """Log all the messages that were waiting on start
        """
        # clear all the previous messages
        BrickModel.delete_all()

        bricks_info: Dict[str, ModuleInfo] = BrickHelper.get_all_bricks()
        for brick_name, brick_info in bricks_info.items():
            # skip app and skeleton 'bricks'
            if brick_name == 'app' or brick_name == 'skeleton':
                continue
            cls._init_brick_model(brick_name, brick_info['path'])

        for brick_message in cls._waiting_messages:
            cls._log_brick_message(brick_message)

        cls._waiting_messages = []

    @classmethod
    def _init_brick_model(cls, name: str, path: str) -> BrickModel:
        brick_model: BrickModel = cls._get_or_create_brick(name, path)
        brick_model.clear_messages()
        return brick_model.save()

    @classmethod
    def _get_or_create_brick(cls, name: str, path: str) -> BrickModel:
        brick: BrickModel = BrickModel.find_by_name(name)

        if brick is None:
            brick = BrickModel()
            brick.name = name
            brick.path = path
            brick.status = 'SUCCESS'

        return brick

    @classmethod
    def get_all_brick_models(cls) -> List[BrickModel]:
        return list(BrickModel.select())

    @classmethod
    def get_brick_model(cls, name: str) -> BrickModel:
        return BrickModel.find_by_name(name)

    @classmethod
    def import_all_modules(cls):
        bricks_info: Dict[str, ModuleInfo] = BrickHelper.get_all_bricks()
        for brick_name, brick_info in bricks_info.items():
            _, files = Utils.walk_dir(os.path.join(brick_info['path'], "src"))
            for py_file in files:
                parts = py_file.split("/src/")[-1].split("/")
                parts[-1] = os.path.splitext(parts[-1])[0]  # remove .py extension
                module_name = ".".join(parts)
                try:
                    importlib.import_module(module_name)
                # On module load error, log an error but don't stop the app szo a brick won't break the whole app
                except Exception as err:
                    cls.log_brick_message(
                        brick_name=brick_name, brick_path=brick_info['path'],
                        message=f"Cannot import module {module_name}. Skipping brick load. Error: {err}",
                        status='CRITICAL')
                    traceback.print_exc()
                    # stop the brick load and go to next brick
                    break
                    # raise Exception(f"Cannot import module {module_name}.") from err
