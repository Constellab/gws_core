# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import pymysql

from peewee import SqliteDatabase, MySQLDatabase, DatabaseProxy
from playhouse.sqlite_ext import JSONField as SQLiteJSONField
from playhouse.mysql_ext import JSONField as MySQLJSONField
from gws.settings import Settings
settings = Settings.retrieve()

# ####################################################################
#
# AbstractDbManager class
#
# ####################################################################

class AbstractDbManager:
    """
    DbManager class. Provides backend feature for managing databases. 
    """

    @classmethod
    def init(cls, engine:str="sqlite3"):
        if engine == "sqlite3":
            _db = SqliteDatabase(cls.get_sqlite3_db_path())
            cls.JSONField = SQLiteJSONField
        elif engine in ["mariadb", "mysql"]:
            _db = MySQLDatabase(
                cls._db_name,
                user='gws',
                password='gencovery',
                host=settings.get_maria_db_host(), 
                port=3306
            )
            cls.JSONField = MySQLJSONField
        else:
            raise Exception("gws.db.model.DbManager", "init", f"Db engine '{engine}' is not valid")

        cls.db.initialize(_db)
        cls._engine = engine
        
    @classmethod
    def create_maria_db(cls):
        """
        Creates maria database
        """

        if not cls._engine == "mariadb":
            raise Exception("gws.db.manager.DbManager", "create_maria_database", "Db engine is not mariab")
        
        conn = pymysql.connect(host='mariadb', port=3306, user="root", password="gencovery")
        conn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {cls._db_name}")
        conn.cursor().execute(f"GRANT ALL PRIVILEGES ON ${cls._db_name}.* TO 'gws'@'localhost';")
        conn.close()

    @classmethod
    def get_sqlite3_db_path(cls):
        db_dir = settings.get_sqlite3_db_dir()
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db_path = os.path.join(db_dir, cls._db_name + ".sqlite3")
        return db_path

