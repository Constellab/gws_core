# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Type

from gws_core.core.db.db_config import DbConfig, DbMode
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings

from .db_manager import AbstractDbManager


class DbManagerService():
    # store the db manager that ware initialized and check that the keys are unique
    _db_managers: Dict[str, Type[AbstractDbManager]] = {}

    @classmethod
    def init_all_db(cls) -> None:
        """
        Initialize the databases of all DbManagers that inherit the  AbstractDbManager

        :param test: Set `True` to use the test db. The non-test db is used instead
        :type test: `bool`
        """

        # define DB mode
        mode: DbMode = cls.get_db_mode()

        for manager in cls._get_db_manager_classes():
            cls._init_db(manager, mode)

    @classmethod
    def _init_db(cls, db_manager_type: Type[AbstractDbManager], mode: DbMode) -> None:
        unique_name = db_manager_type.get_unique_name()

        if unique_name in cls._db_managers:
            Logger.warning(f"The db manager with the name '{unique_name}' was already initialized")
            return
            #raise Exception(f"The db manager with the name '{unique_name}' was already initialized")

        db_manager_type.init(mode)

        # save the db manager as initiliazed
        cls._db_managers[unique_name] = db_manager_type

    @classmethod
    def _get_db_manager_classes(cls) -> List[Type[AbstractDbManager]]:
        """ Get all the classes that inherit this class """
        return AbstractDbManager.inheritors()

    @classmethod
    def get_db_manager_config(cls, db_manager_name: str) -> DbConfig:

        if not db_manager_name in cls._db_managers:
            raise BadRequestException(
                f"The db manager with the name '{db_manager_name}' doesn't exist")

        return cls._db_managers[db_manager_name].get_config(cls.get_db_mode())

    @classmethod
    def get_db_mode(cls) -> DbMode:
        settings = Settings.get_instance()
        if settings.is_test:
            return 'test'
        elif settings.is_prod:
            return 'prod'
        else:
            return 'dev'
