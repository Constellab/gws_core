# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ...model.model_service import ModelService
from ...study.study import Study
from ...user.auth_service import AuthService
from ...user.user import User
from ...user.user_service import UserService
from ..exception.exceptions import BadRequestException
from ..utils.settings import Settings


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

        ModelService.register_all_processes_and_resources()

        settings = Settings.retrieve()
        if not settings.is_dev:
            raise BadRequestException(
                "The unit tests can only be initialized in dev mode")

        study = Study.get_default_instance()
        UserService.create_owner_and_sysuser()
        user = User.get_sysuser()
        # refresh user information from DB
        AuthService.authenticate(
            uri=user.uri, console_token=user.console_token)

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
