# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import shutil

from ...core.exception.exceptions import BadRequestException
from ...core.model.base_model_service import BaseModelService
from ...core.utils.settings import Settings
from ...lab.system_service import SystemService
from ...user.auth_service import AuthService
from ...user.user import User


class Console:
    """
    Console class.

    Provides functionalities to initilize console environments
    """

    user: User = None

    @classmethod
    def init(cls, user: User = None):
        """
        This function initializes objects for unit testing
        """

        settings = Settings.retrieve()
        if not settings.is_dev:
            raise BadRequestException(
                "The unit tests can only be initialized in dev mode")

        SystemService.init()

        if user is None:
            user = User.get_sysuser()

        # refresh user information from DB
        AuthService.authenticate(id=user.id)

        cls.user = user

    @classmethod
    def create_tables(cls, models: list = None):
        """
        Create tables
        """

        BaseModelService.create_tables(models)

    @classmethod
    def drop_tables(cls, models: list = None):
        """
        Drops tables
        """

        BaseModelService.drop_tables(models)

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
    def print(cls, text):
        """
        Print test title
        """
        print(f"---- Test: {text} ----")
