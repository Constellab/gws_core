# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import importlib
from ..core.console.console import Console
from ..user.user import User
from ..core.exception.exceptions import BadRequestException
from ..user.auth_service import AuthService


class Notebook(Console):
    """
    Notebook class.

    Provides functionalities to initilize in notebook environnments
    """

    @classmethod
    def authenticate(cls, email=None):
        # refresh user information from DB
        try:
            user = User.get(User.email == email)
        except:
            raise BadRequestException("User not found. Authentication failed!")

        try:
            AuthService.authenticate(
                id=user.id, console_token=user.console_token)
        except:
            raise BadRequestException("Authentication failed!")

        cls.user = user
