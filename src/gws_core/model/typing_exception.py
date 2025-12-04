from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.model.typing_name import TypingNameObj


class TypingNotFoundException(BadRequestException):
    """Exception raised when the before task returned false and all the input of the task where provided

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    :return: [description]
    :rtype: [type]
    """

    def __init__(self, typing_name: str) -> None:
        typing_name_obj = TypingNameObj.from_typing_name(typing_name)
        super().__init__(
            detail=GWSException.TYPING_NOT_FOUND.value,
            unique_code=GWSException.TYPING_NOT_FOUND.name,
            detail_args={
                "unique_name": typing_name_obj.unique_name,
                "object_type": typing_name_obj.object_type,
                "brick_name": typing_name_obj.brick_name,
            },
        )
