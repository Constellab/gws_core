
from fastapi.requests import Request
from fastapi.security.utils import get_authorization_scheme_param

from gws_core.core.exception.exceptions.forbidden_exception import ForbiddenException
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.credentials.credentials_type import CredentialsDataLab
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user_service import UserService


class ExternalLabAuth:
    API_KEY_HEADER_NAME = "Authorization"
    API_KEY_HEADER_PREFIX = "api-key"
    USER_ID_HEADER_NAME = "X-User-Id"

    @classmethod
    def check_auth(cls, request: Request) -> None:
        """Method to check the space api key in the request header

        :param api_key: [description], defaults to Depends(oauth2_space_header_scheme)
        :type api_key: str, optional
        :raises UnauthorizedException: [description]
        """

        cls._get_and_check_credentials(request)
        cls._authenticate_user(request)

    @classmethod
    def _get_and_check_credentials(cls, request: Request) -> CredentialsDataLab:
        api_key = cls._get_and_check_api_key(request)

        credentials = CredentialsService.get_lab_credentials_data_by_api_key(api_key)

        if not credentials:
            raise ForbiddenException("Not authorized. Invalid request.")

        return credentials

    @classmethod
    def _get_and_check_api_key(cls, request: Request) -> str:
        header_authorization: str = request.headers.get(ExternalLabAuth.API_KEY_HEADER_NAME)
        header_scheme, header_param = get_authorization_scheme_param(header_authorization)

        if header_scheme.lower() == ExternalLabAuth.API_KEY_HEADER_PREFIX:
            return header_param

        raise ForbiddenException("Not authorized. Invalid request.")

    @classmethod
    def _authenticate_user(cls, request: Request) -> None:
        user_id = cls._get_user_id(request)

        if not user_id:
            raise ForbiddenException("Not authorized. User information missing.")

        user = UserService.get_or_import_user_info(user_id)

        CurrentUserService.set_auth_user(user)

    @classmethod
    def _get_user_id(cls, request: Request) -> str | None:
        return request.headers.get(ExternalLabAuth.USER_ID_HEADER_NAME)

    @classmethod
    def get_auth_headers(cls, api_key: str, user_id: str) -> dict:
        return {
            cls.API_KEY_HEADER_NAME: f"{cls.API_KEY_HEADER_PREFIX} {api_key}",
            cls.USER_ID_HEADER_NAME: user_id,
        }
