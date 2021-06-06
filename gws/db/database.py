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



# ####################################################################
#
# DbManager class
#
# ####################################################################

class DbManager:
    """
    DbManager class. Provides backend feature for managing databases. 
    """
    
    db = DatabaseProxy()
    JSONField = None
    _engine = None
 
    @classmethod
    def init(cls, engine:str="sqlite3"):
        settings = Settings.retrieve()

        if engine == "sqlite3":
            db_path = os.path.join(
                settings.get_sqlite3_db_dir(),
                settings.SQLITE3_DB_NAME
            )
            _db = SqliteDatabase(db_path)
            cls.JSONField = SQLiteJSONField
        elif engine in ["mariadb", "mysql"]:
            _db = MySQLDatabase(
                "gws",
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
            raise Exception("gws.db.model.DbManager", "create_maria_database", "Db engine is not mariab")
        
        db_name = "gws"
        conn = pymysql.connect(host='mariadb', port=3306, user="root", password="gencovery")
        conn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        conn.cursor().execute(f"GRANT ALL PRIVILEGES ON ${db_name}.* TO 'gws'@'localhost';")
        conn.close()

DbManager.init("sqlite3")
