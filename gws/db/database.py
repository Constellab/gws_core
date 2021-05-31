# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import SqliteDatabase, MySQLDatabase, DatabaseProxy
from playhouse.sqlite_ext import JSONField as SQLiteJSONField
from playhouse.mysql_ext import JSONField as MySQLJSONField

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
        from gws.settings import Settings
        if engine == "sqlite3":
            settings = Settings.retrieve()
            _db = SqliteDatabase(settings.db_path)
            cls.JSONField = SQLiteJSONField
        elif engine in ["mariadb", "mysql"]:
            _db = MySQLDatabase("gws", user='gws', password='gencovery', host='mariadb', port=3306)
            cls.JSONField = MySQLJSONField
        else:
            raise Exception("gws.db.model.DbManager", "init", f"Db engine '{engine}' is not valid")

        cls.db.initialize(_db)
        cls._engine = engine

DbManager.init("sqlite3")
