from gws_core.brick.brick_service import BrickService
from gws_core.core.db.db_config import DbMode
from gws_core.core.db.migration.db_migration_service import DbMigrationService
from gws_core.core.model.base_model_service import BaseModelService
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings

from .abstract_db_manager import AbstractDbManager


class DbManagerService:
    @classmethod
    def init_all_db(cls, full_init: bool = True) -> None:
        """
        Initialize the databases of all DbManagers that inherit the  AbstractDbManager

        :param full_init: If true, the migration and table creation will be done. If false, only the connection to the DB will be done. Defaults to True.
        :type full_init: bool, optional
        """

        # define DB mode
        mode: DbMode = cls.get_db_mode()

        db_managers = cls._get_db_manager_classes()

        # remove db_managers that are not auto_init
        db_managers = [db for db in db_managers if db.auto_init()]

        # sort the db_managers to have the lazy db at the end of the list
        db_managers.sort(key=lambda x: x.is_lazy_init())

        for manager in db_managers:
            cls._init_db_with_error_handling(manager, mode, full_init=full_init)

    @classmethod
    def init_db(
        cls,
        db_manager: AbstractDbManager,
        full_init: bool = True,
        ignore_error: bool = False,
    ) -> bool:
        """
        Initialize the database of the provided DbManager

        :param db_manager: The DbManager instance to initialize
        :type db_manager: AbstractDbManager
        :param full_init: If true, the migration and table creation will be done. If false, only the connection to the DB will be done. Defaults to True.
        :type full_init: bool, optional
        :param ignore_error: If true, errors will be logged but not raised. Defaults to False.
        :type ignore_error: bool, optional
        """

        mode: DbMode = cls.get_db_mode()
        return cls._init_db_with_error_handling(
            db_manager, mode, full_init=full_init, ignore_error=ignore_error
        )

    @classmethod
    def _init_db_with_error_handling(
        cls,
        db_manager: AbstractDbManager,
        mode: DbMode,
        full_init: bool,
        ignore_error: bool = False,
    ) -> bool:
        """Wrapper that calls _init_db with error handling and logging."""
        try:
            cls._init_db(db_manager, mode, full_init)
        except Exception as err:
            if ignore_error:
                return False
            unique_name = db_manager.get_unique_name()
            error = f"Error while initializing the db '{unique_name}'. Error: {err}"
            cls._handle_db_init_error(db_manager, err, error)

        return True

    @classmethod
    def _init_db(
        cls, db_manager: AbstractDbManager, mode: DbMode, full_init: bool
    ) -> None:
        """Core initialization logic that raises exceptions directly."""
        unique_name = db_manager.get_unique_name()

        # initialize the db manager and connect to the db
        db_manager.init(mode)

        if full_init:
            # call the migration for that db manager
            DbMigrationService.migrate(db_manager)

            # create the tables for the models of this db manager
            BaseModelService.create_database_tables(db_manager)

        Logger.debug(f"Db manager '{unique_name}' initialized in '{mode}' mode")

    @classmethod
    def _handle_db_init_error(
        cls,
        db_manager: AbstractDbManager,
        err: Exception,
        error_message: str,
    ) -> None:
        if db_manager.is_lazy_init():
            Logger.log_exception_stack_trace(err)
            BrickService.log_brick_critical(
                db_manager,
                f"{error_message}. The db manager is lazy, so skipping initialization.",
            )
            return
        else:
            raise Exception(error_message)

    @classmethod
    def _get_db_manager_classes(cls) -> list[AbstractDbManager]:
        """Get all the classes that inherit this class"""
        return list(AbstractDbManager.get_db_managers())

    @classmethod
    def get_db_mode(cls) -> DbMode:
        settings = Settings.get_instance()
        if settings.is_test:
            return "test"
        elif settings.is_prod_mode():
            return "prod"
        else:
            return "dev"
