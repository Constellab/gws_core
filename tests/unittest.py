# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from .exception.exceptions.bad_request_exception import BadRequestException

from .service.model_service import ModelService
from .utils.settings import Settings
from .study import Study
from .user import User


class GTest:
    """
    GTest class.

    Provides functionalities to initilize unit testing envirninments
    """

    user: User = None
    study: Study = None

    @classmethod
    def init(cls, admin_user=False):
        """
        This function initializes objects for unit testing
        """

        settings = Settings.retrieve()
        if not settings.is_dev:
            raise BadRequestException(
                "The unit tests can only be initialized in dev mode")

        study = Study.get_default_instance()
        User.create_owner_and_sysuser()
        user = User.get_sysuser()
        # refresh user information from DB
        User.authenticate(uri=user.uri, console_token=user.console_token)

        cls.user = user
        cls.study = study

    @classmethod
    def create_tables(cls, models: list = None):
        """
        Create tables
        """

        ModelService.create_tables(models)

    @classmethod
    def drop_tables(cls, models: list = None):
        """
        Drops tables
        """

        ModelService.drop_tables(models)

    @classmethod
    def print(cls, text):
        """
        Print test title
        """

        text = "Test: " + text

        n = max((len(text)+3), 64)
        stars = "*" * n
        print("\n" + stars)
        print("*")
        print(f"* {text} ")
        print("*")
        print(stars + "\n")
