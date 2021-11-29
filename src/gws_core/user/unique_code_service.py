

from typing import Any, Dict, TypedDict

from fastapi import status

from ..core.exception.exceptions.base_http_exception import BaseHTTPException
from ..core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from ..core.exception.gws_exceptions import GWSException
from ..core.utils.utils import Utils


class CodeObject(TypedDict):
    user_id: str
    obj: Any


class UniqueCodeService():

    # dictionary where key = generated code
    _generated_codes: Dict[str, CodeObject] = {}

    @classmethod
    def generate_code(cls, user_id: str, obj: Any) -> str:
        """Generate a unique code for a user.

        :param user_id: id of the user to generate code
        :type user_id: str
        :param obj: object link to the generation.
        :type obj: Any
        :return: [description]
        :rtype: str
        """
        uuid = Utils.generate_uuid()
        cls._generated_codes[uuid] = {'user_id': user_id, 'obj': obj}
        return uuid

    @classmethod
    def check_code(cls, code: str) -> CodeObject:
        """check if a code is valid, if yes, return the object containing user_id and obj, and unvalidate the code. If not valid, throw an HttpUnauthorized exception
        """

        if not code in cls._generated_codes:
            raise InvalidUniqueCodeException()

        code_obj = cls._generated_codes[code]
        del cls._generated_codes[code]
        return code_obj


class InvalidUniqueCodeException(BaseHTTPException):

    def __init__(self) -> None:
        super().__init__(
            http_status_code=status.HTTP_403_FORBIDDEN,
            detail=GWSException.INVALID_UNIQUE_CODE.value,
            unique_code=GWSException.INVALID_UNIQUE_CODE.name)
