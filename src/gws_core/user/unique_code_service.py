

from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import status
from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.string_helper import StringHelper
from gws_core.user.current_user_service import CurrentUserService

from ..core.exception.exceptions.base_http_exception import BaseHTTPException
from ..core.exception.gws_exceptions import GWSException


class CodeObject(BaseModelDTO):
    user_id: str
    obj: Any
    expiration_date: datetime


class UniqueCodeService():

    # dictionary where key = generated code
    _generated_codes: Dict[str, CodeObject] = {}

    @classmethod
    def generate_code_current_user(cls, obj: Any, validity_duration: int) -> str:
        return cls.generate_code(CurrentUserService.get_current_user().id, obj, validity_duration)

    @classmethod
    def generate_code(cls, user_id: str, obj: Any, validity_duration: int) -> str:
        """Generate a unique code for a user.

        :param user_id: id of the user to generate code
        :type user_id: str
        :param obj: object link to the generation.
        :type obj: Any
        :param validity_duration: validity duration in second of the code
        :type validity_duration: Any
        :return: [description]
        :rtype: str
        """
        uuid = StringHelper.generate_uuid()

        expriation_date = datetime.now() + timedelta(seconds=validity_duration)
        cls._generated_codes[uuid] = CodeObject(user_id=user_id, obj=obj, expiration_date=expriation_date)
        return uuid

    @classmethod
    def check_code(cls, code: str) -> CodeObject:
        """check if a code is valid, if yes, return the object containing user_id and obj, and unvalidate the code. If not valid, throw an HttpUnauthorized exception
        """

        if not code in cls._generated_codes:
            raise InvalidUniqueCodeException()

        code_obj = cls._generated_codes[code]
        del cls._generated_codes[code]

        if datetime.now() > code_obj.expiration_date:
            raise InvalidUniqueCodeException()

        return code_obj


class InvalidUniqueCodeException(BaseHTTPException):

    def __init__(self) -> None:
        super().__init__(
            http_status_code=status.HTTP_403_FORBIDDEN,
            detail=GWSException.INVALID_UNIQUE_CODE.value,
            unique_code=GWSException.INVALID_UNIQUE_CODE.name)
