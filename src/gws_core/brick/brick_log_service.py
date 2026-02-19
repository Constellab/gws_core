from time import time
from typing import Any

from gws_core.brick.brick_dto import BrickMessageStatus
from gws_core.brick.brick_model import BrickModel
from gws_core.core.model.model_dto import BaseModelDTO

from ..core.utils.logger import Logger
from ..lab.system_status import SystemStatus
from .brick_helper import BrickHelper


class WaitingMessage(BaseModelDTO):
    brick_name: str
    message: str
    status: BrickMessageStatus
    timestamp: float


class BrickLogService:
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

        brick_model: BrickModel = BrickModel.find_by_name(brick_message.brick_name)

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
    def log_waiting_messages(cls) -> None:
        for brick_message in cls._waiting_messages:
            cls._log_brick_message(brick_message)

        cls._waiting_messages = []
