# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import shutil

from ...lab.system_service import SystemService
from ...core.exception.exceptions import BadRequestException
from ...core.utils.settings import Settings
from ...model.model_service import ModelService
from ...study.study_dto import StudyDto
from ...user.auth_service import AuthService
from ...user.user import User
from ...user.user_service import UserService

class Console:
    """
    Console class.

    Provides functionalities to initilize console environments
    """

    user: User = None

    @classmethod
    def init(cls, clean_db: bool=False, user: User=None):
        """
        This function initializes objects for unit testing
        """

        if clean_db:
            cls.drop_tables()
            cls.create_tables()
            
        settings = Settings.retrieve()
        if not settings.is_dev:
            raise BadRequestException(
                "The unit tests can only be initialized in dev mode")

        SystemService.init()

        if user is None:
            user = User.get_sysuser()

        # refresh user information from DB
        AuthService.authenticate(
            uri=user.uri, console_token=user.console_token)

        cls.user = user

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
    def delete_data_and_temp_folder(cls):
        """
        Drops tables
        """
        settings: Settings = Settings.retrieve()

        if not settings.is_test:
            raise Exception('Can only delete the data and temp folder in test env')
        shutil.rmtree(path=settings.get_data_dir(), ignore_errors=True)
        SystemService.delete_temp_folder()

    @classmethod
    def default_study_dto(cls) -> StudyDto:
        """
        Get a default study DTO
        """
        return StudyDto(uri="3b4a462a-d2e2-4859-9837-9303b4a51889", title="Default study",
                        description="Study description")

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
