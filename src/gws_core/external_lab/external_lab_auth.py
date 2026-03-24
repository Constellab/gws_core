
from fastapi.requests import Request
from fastapi.security.utils import get_authorization_scheme_param

from gws_core.core.exception.exceptions.forbidden_exception import ForbiddenException
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.lab.lab_model.lab_model import LabModel
from gws_core.user.auth_context import AuthContextExternalLab
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User
from gws_core.user.user_service import UserService


class ExternalLabAuth:
    API_KEY_HEADER_NAME = "Authorization"
    API_KEY_HEADER_PREFIX = "api-key"
    USER_ID_HEADER_NAME = "X-User-Id"

    @classmethod
    def check_auth(cls, request: Request) -> None:
        """Method to check the external lab api key and user in the request header.

        Validates the API key credentials, resolves the associated LabModel,
        authenticates the user, then sets an AuthContextExternalLab in the current session.
        """

        lab = cls._get_and_check_lab(request)
        user = cls._get_and_check_user(request)

        auth_context = AuthContextExternalLab(user=user, lab=lab)
        CurrentUserService.set_auth_context(auth_context)

    @classmethod
    def _get_and_check_lab(cls, request: Request) -> LabModel:
        """Validate the API key and resolve the LabModel associated with the credentials."""
        api_key = cls._get_and_check_api_key(request)

        credentials = CredentialsService.get_lab_credentials_by_api_key(api_key)

        if not credentials:
            raise ForbiddenException("Not authorized. Invalid request.")

        lab = LabModel.get_or_none(LabModel.credentials == credentials.id)

        if not lab:
            raise ForbiddenException("Not authorized. No lab associated with these credentials.")

        return lab

    @classmethod
    def _get_and_check_api_key(cls, request: Request) -> str:
        header_authorization: str = request.headers.get(ExternalLabAuth.API_KEY_HEADER_NAME)
        header_scheme, header_param = get_authorization_scheme_param(header_authorization)

        if header_scheme.lower() == ExternalLabAuth.API_KEY_HEADER_PREFIX:
            return header_param

        raise ForbiddenException("Not authorized. Invalid request.")

    @classmethod
    def _get_and_check_user(cls, request: Request) -> User:
        """Get user from X-User-Id header and resolve/import them."""
        user_id = request.headers.get(ExternalLabAuth.USER_ID_HEADER_NAME)

        if not user_id:
            raise ForbiddenException("Not authorized. User information missing.")

        return UserService.get_or_import_user_info(user_id)

    @classmethod
    def get_auth_headers(cls, api_key: str, user_id: str) -> dict:
        return {
            cls.API_KEY_HEADER_NAME: f"{cls.API_KEY_HEADER_PREFIX} {api_key}",
            cls.USER_ID_HEADER_NAME: user_id,
        }
