# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import shutil

from gws_core.core.db.db_manager import DbManager
from gws_core.core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from gws_core.model.model_service import ModelService
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User
from gws_core.user.user_service import UserService

from ..core.utils.settings import Settings


class SystemService:

    @classmethod
    def init(cls):
        """
        Init method init all the api.
         - create all the table if not exists
         - register the processes and resources
         - create the sysuser if not exists
        """
        settings: Settings = Settings.retrieve()
        DbManager.init_all_db(test=settings.is_test)

        cls.create_all_tables()
        ModelService.register_all_processes_and_resources()
        UserService.create_sysuser()

    @classmethod
    def create_all_tables(cls):
        """
        Create tables
        """

        ModelService.create_tables()

    @classmethod
    def drop_all_tables(cls):
        """
        Drops tables
        """
        settings: Settings = Settings.retrieve()
        if settings.is_prod:
            raise Exception('Cannot drop all table in prod env')

        ModelService.drop_tables()

    @classmethod
    def delete_data_and_temp_folder(cls):
        """
        Drops tables
        """
        settings: Settings = Settings.retrieve()

        if settings.is_prod:
            raise Exception('Cannot delete the data and temp folder in prod environment')
        shutil.rmtree(path=settings.get_data_dir(), ignore_errors=True)
        shutil.rmtree(path=settings.get_root_temp_dir(), ignore_errors=True)

    @classmethod
    def reset_dev_envionment(cls) -> None:
        settings: Settings = Settings.retrieve()

        if not settings.is_dev:
            raise UnauthorizedException('The reset method can only be called in dev environment')

        user: User = CurrentUserService.get_and_check_current_user()

        cls.delete_data_and_temp_folder()
        cls.drop_all_tables()

        cls.init()

        UserService.create_user_if_not_exists(user.to_user_data_dict())
