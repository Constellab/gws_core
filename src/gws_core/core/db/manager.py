# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type

from peewee import DatabaseProxy, MySQLDatabase, SqliteDatabase
from playhouse.shortcuts import ReconnectMixin
from ..utils.settings import Settings

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
    _DEFAULT_DB_ENGINE = "mariadb"
    _DEFAULT_DB_NAME = "gws_core"
    __TEST_DB_NAME = "test_gws" # Keep private and constant => All models inherit the same test DB
    _engine = None
    _mariadb_config = {
        "user": _DEFAULT_DB_NAME,
        "password": "gencovery"
    }
    _db_name = _DEFAULT_DB_NAME
    

    @classmethod
    def init(cls, engine: str = None, test: bool = False):
        """ Initialize the DbManager """

        cls._db_name = cls.__TEST_DB_NAME if test else cls._DEFAULT_DB_NAME
        cls._mariadb_config["user"] = cls._db_name

        if engine:
            cls._engine = engine
        if not cls._engine:
            cls._engine = cls._DEFAULT_DB_ENGINE
        if cls._engine == "sqlite3":
            db_path = cls.get_sqlite3_db_path()
            print(db_path)
            _db = SqliteDatabase(db_path)
        elif cls._engine in ["mariadb", "mysql"]:
            _db = ReconnectMySQLDatabase(
                cls._db_name,
                user=cls._mariadb_config["user"],
                password=cls._mariadb_config["password"],
                host=cls.get_maria_db_host(),
                port=3306
            )
        else:
            raise Exception("gws.db.model.DbManager", "init",
                            f"Db engine '{cls._engine}' is not valid")
        cls.db.initialize(_db)

    @staticmethod
    def init_all_db(test: bool=False) -> None:
        """
        Initialize all the database

        Propagate to all AbstractDbManager subclasses
        Requires that all the bricks' modules are loaded on Application stratup.
        See gws_core.manage.load_settings()

        :param test: Set `True` to use the test db. The non-test db is used instead
        :type test: `bool`
        """

        for sub_db_manager in AbstractDbManager.inheritors():
            sub_db_manager.init(test=test)

    @classmethod
    def inheritors(cls) -> List[Type['DbManager']]:
        """ Get all the classes that inherit this class """
        return set(cls.__subclasses__()).union(
            [s for c in cls.__subclasses__() for s in c.inheritors()])

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

    @classmethod
    def get_db(cls):
        """ Get the db object """

        return cls.db

    @classmethod
    def get_db_name(cls):
        """ Get the current db name """

        return cls._db_name

    @classmethod
    def get_engine(cls):
        """ Get the current db engine """

        return cls._engine

    @classmethod
    def get_maria_db_host(cls):
        """ Get the current maria db host address """

        settings = Settings.retrieve()
        return settings.get_maria_db_host(cls._db_name)

    @classmethod
    def get_sqlite3_db_path(cls):
        """ Get the current current sqlite3 db path """

        settings = Settings.retrieve()
        db_path = settings.get_sqlite3_db_path(cls._db_name)
        return db_path

    # -- I --

    @classmethod
    def is_sqlite_engine(cls):
        """ Test if the sqlite3 engine is active """

        return cls._engine == "sqlite3"

    @classmethod
    def is_mysql_engine(cls):
        """ Test if the mysql engine is active """

        return cls._engine in ["mariadb", "mysql"]
