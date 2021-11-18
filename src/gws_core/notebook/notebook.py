# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ..core.console.console import Console
from ..core.exception.exceptions import BadRequestException
from ..user.auth_service import AuthService
from ..user.user import User


class Notebook(Console):
    """
    Notebook class.

    Provides functionalities to initilize in notebook environnments
    """

    @classmethod
    def authenticate(cls, email=None):
        # refresh user information from DB
        try:
            user: User = User.get(User.email == email)
        except:
            raise BadRequestException("User not found. Authentication failed!")

        try:
            AuthService.authenticate(id=user.id)
        except:
            raise BadRequestException("Authentication failed!")

        cls.user = user
