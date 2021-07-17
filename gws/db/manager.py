# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import pymysql
import subprocess

from peewee import SqliteDatabase, MySQLDatabase, DatabaseProxy
from gws.settings import Settings

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
    _engine = None
    _mariadb_config = {
        "user": "gws",
        "password": "gencovery"
    }
    _db_name = "gws"

    @classmethod
    def init(cls, engine:str=None, mode: str=None):
        """ Initialize the DbManager """
        
        if engine:
            cls._engine = engine
        if not cls._engine:
            cls._engine = "sqlite3"
        if cls._engine == "sqlite3":
            db_path = cls.get_sqlite3_db_path(mode=mode)
            _db = SqliteDatabase(db_path)
        elif cls._engine in ["mariadb", "mysql"]:
            _db = MySQLDatabase(
                cls._db_name,
                user        = cls._mariadb_config["user"],
                password    = cls._mariadb_config["password"],
                host        = cls.get_maria_db_host(),
                port        = 3306
            )
        else:
            raise Exception("gws.db.model.DbManager", "init", f"Db engine '{cls._engine}' is not valid")
        cls.db.initialize(_db)

    # -- C --

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
        """ Get the db name """

        return cls._db_name

    @classmethod
    def get_engine(cls):
        """ Get the db engine """

        return cls._engine

    @classmethod
    def get_maria_db_host(cls):
        """ Get maria db host address """

        settings = Settings.retrieve()
        return settings.get_maria_db_host( cls._db_name )

    @classmethod
    def get_sqlite3_db_path(cls, mode:str=None):
        """ Get the sqlite3 db path """

        settings = Settings.retrieve()
        if mode:
            if mode == "prod":
                db_path = settings.get_sqlite3_prod_db_path(cls._db_name)
            else:
                db_path = settings.get_sqlite3_dev_db_path(cls._db_name)
        else:
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

