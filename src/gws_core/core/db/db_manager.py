# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import Dict, List, Type

from gws_core.core.utils.utils import Utils
from peewee import DatabaseProxy, MySQLDatabase
from playhouse.shortcuts import ReconnectMixin

from .db_config import DbConfig, DbMode, SupportedDbEngine

# ####################################################################
#
# ReconnectMySQLDatabase class
#
# ####################################################################


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    """
    MySQLDatabase class.
    Allow to auto-reconnect to the MySQL database.
    """
    pass

# ####################################################################
#
# AbstractDbManager class
#
# ####################################################################


class AbstractDbManager:
    """
    DbManager class. Provides backend feature for managing databases.

    Implementation must define fillowing properties

    :property db: Database Proxy
    :type db: `DatabaseProxy`
    """

    db = DatabaseProxy()

    mode: DbMode = None

    @classmethod
    @abstractmethod
    def get_config(self, mode: DbMode) -> DbConfig:
        pass

    @classmethod
    @abstractmethod
    def get_unique_name(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def get_brick_name(cls) -> str:
        pass

    @classmethod
    def init(cls, mode: DbMode):
        """ Initialize the DbManager """
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

    @classmethod
    def inheritors(cls) -> List[Type['AbstractDbManager']]:
        """ Get all the classes that inherit this class """
        return set(cls.__subclasses__()).union(
            [s for c in cls.__subclasses__() for s in c.inheritors()])

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

    # -- C --

    # @classmethod
    # def connect_db(cls):
    #     """ Open the db connection """

    #     if cls.db.is_closed():
    #         cls.db.connect()

    # @classmethod
    # def disconnect_db(cls):
    #     """ Close the db connection """

    #     if not cls.db.is_closed():
    #         cls.db.close()

    # @classmethod
    # def create_maria_db(cls):
    #     """
    #     Creates maria database
    #     """

    #     if not cls._engine == "mariadb":
    #         raise Exception("gws.db.manager.DbManager", "create_maria_database", "Db engine is not mariab")

    #     conn = pymysql.connect(host='mariadb', port=3306, user="root", password="gencovery")
    #     conn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {cls._db_name}")
    #     conn.cursor().execute(f"GRANT ALL PRIVILEGES ON ${cls._db_name}.* TO 'gws'@'localhost';")
    #     conn.close()

    # -- D --

    # -- G --
