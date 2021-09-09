import inspect
import os
import uuid
from typing import List

from ..utils.utils import Utils

CODE_SEPARATOR = '.'


class ExceptionHelper():

    @classmethod
    def generate_unique_code_from_exception(cls) -> str:
        """Generate a unique exception code from the stack trace

        :return: BRICK_NAME.FILE_NAME.METHOD_NAME
        :rtype: str
        """
        trace: List = inspect.trace()
        if not trace:
            return ""

        frame_info: inspect.FrameInfo = trace[-1]

        if frame_info is None:
            return ""

        code = os.path.split(
            frame_info.filename)[-1] + CODE_SEPARATOR + frame_info.function

        return cls.get_unique_code_for_brick(code)

    @classmethod
    def get_unique_code_for_brick(cls, code: str) -> str:
        """Convert the code to a unique code by adding the brick name before the code

        :param code: exception code
        :type code: str
        :return: exception unique code
        :rtype: str
        """
        return cls._get_brick_name() + CODE_SEPARATOR + code

    @classmethod
    def _get_brick_name(cls) -> str:
        """Retrieve the brick name of the raised exception from the full filename
        of the trace

        :return: brick name
        :rtype: str
        """
        frame_info: inspect.FrameInfo = inspect.trace()[-1]

        return Utils.get_brick_name(frame_info[0])

    @classmethod
    def unique_code_separator(cls) -> str:
        return CODE_SEPARATOR

    @classmethod
    def generate_instance_id(cls) -> str:
        return str(uuid.uuid4())
