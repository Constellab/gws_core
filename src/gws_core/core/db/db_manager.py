

from abc import abstractmethod
from typing import Set, Type

from gws_core.core.utils.utils import Utils
from peewee import DatabaseProxy, MySQLDatabase
from playhouse.shortcuts import ReconnectMixin

from .db_config import DbConfig, DbMode, SupportedDbEngine


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    """
    MySQLDatabase class.
    Allow to auto-reconnect to the MySQL database.
    """
    pass


class AbstractDbManager:
    """
    DbManager class. Provides backend feature for managing databases.

    Implementation must define fillowing properties

    :property db: Database Proxy
    :type db: `DatabaseProxy`
    """

    db: DatabaseProxy = None

    mode: DbMode = None

    # If True, the db will be initialized after the app start, and app won't fail if db is not available
    # If False, the db will be initialized immediately (not recommended), and app fails if db is not available
    lazy_init = True

    _is_initialized = False

    @classmethod
    @abstractmethod
    def get_config(cls, mode: DbMode) -> DbConfig:
        pass

    @classmethod
    def get_unique_name(cls) -> str:
        return cls.get_brick_name() + '-' + cls.get_name()

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """
        Return the name of the DbManager.
        The combination of brick name and unique name must be unique accross all DbManager inheritors.
        """

    @classmethod
    @abstractmethod
    def get_brick_name(cls) -> str:
        pass

    @classmethod
    def init(cls, mode: DbMode):
        """ Initialize the DbManager """

        if cls.is_initialized():
            return
        cls.mode = mode
        db_config = cls.get_config(mode)

        if db_config is None:
            raise Exception("The db config is not provided, did you implement the 'get_config' in your DbManager ?")

        if not Utils.value_is_in_literal(db_config["engine"], SupportedDbEngine):
            raise Exception("gws.db.model.DbManager", "init",
                            f"Db engine '{db_config['engine']}' is not valid")

        _db = ReconnectMySQLDatabase(
            db_config["db_name"],
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config['port']
        )
        cls.db.initialize(_db)
        cls._is_initialized = True

    @classmethod
    def inheritors(cls) -> Set[Type['AbstractDbManager']]:
        """ Get all the classes that inherit this class """
        db_managers = set(cls.__subclasses__()).union(
            [s for c in cls.__subclasses__() for s in c.inheritors()])

        # filter out abstract classes, check if get_unique_name and get_brick_name return a value
        return {db_manager for db_manager in db_managers
                if db_manager.db is not None
                and db_manager.get_unique_name() is not None
                and db_manager.get_brick_name() is not None}

    @classmethod
    def get_db(cls) -> DatabaseProxy:
        """ Get the db object """

        return cls.db

    @classmethod
    def get_engine(cls) -> SupportedDbEngine:
        """ Get the db object """

        return cls.get_config(cls.mode)["engine"]

    @classmethod
    def is_mysql_engine(cls):
        """ Test if the mysql engine is active """

        return cls.get_engine() in ["mariadb", "mysql"]

    @classmethod
    def close_db(cls):
        """ Close the db connection """

        if not cls.db.is_closed():
            cls.db.close()

    @classmethod
    def connect_db(cls):
        """ Open the db connection """

        if cls.db.is_closed():
            cls.db.connect()

    @classmethod
    def create_tables(cls, models: list[Type]) -> None:
        """ Create the tables for the provided models """

        if not models or len(models) == 0:
            return

        cls.db.create_tables(models)

    @classmethod
    def drop_tables(cls, models: list[Type]) -> None:
        """ Drop the tables for the provided models """

        if not models or len(models) == 0:
            return

        cls.db.drop_tables(models)

    @classmethod
    def execute_sql(cls, sql: str) -> None:
        """ Execute the provided sql command """

        cls.db.execute_sql(sql)

    @classmethod
    def is_initialized(cls) -> bool:
        """ Return if the db manager was initialized """

        return cls._is_initialized
