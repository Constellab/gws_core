

import shutil

from gws_core.lab.system_status import SystemStatus

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
    def init_complete(cls, user: User = None):
        """
        This function initializes objects for unit testing
        """

        if not Settings.is_dev_mode():
            raise BadRequestException(
                "The unit tests can only be initialized in dev mode")

        SystemService.init()

        if user is None:
            user = User.get_sysuser()

        # refresh user information from DB
        AuthService.authenticate(id=user.id)

        cls.user = user

    @classmethod
    def init(cls):
        """
        This function initializes objects for unit testing
        """

        if not Settings.is_dev_mode():
            raise BadRequestException(
                "The unit tests can only be initialized in dev mode")

        SystemService.init_data_folder()
        SystemStatus.app_is_initialized = True

    @classmethod
    def drop_tables(cls):
        """
        Drops tables
        """

        BaseModelService.drop_tables()

    @classmethod
    def delete_data_and_temp_folder(cls):
        """
        Drops tables
        """
        settings: Settings = Settings.get_instance()

        if not settings.is_test:
            raise Exception('Can only delete the data and temp folder in test env')
        shutil.rmtree(path=settings.get_data_dir(), ignore_errors=True)
        SystemService.delete_temp_folder()
