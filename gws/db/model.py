# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import re

from peewee import SqliteDatabase, DatabaseProxy, Model
from playhouse.sqlite_ext import RowIDField, SearchField, FTS5Model

from playhouse.sqlite_ext import JSONField as SQLiteJSONField
from playhouse.mysql_ext import JSONField as MySQLJSONField

from gws.settings import Settings
from gws.base import Base

# ####################################################################
#
# Misc
#
# ####################################################################

def format_table_name(cls):
    model_name = cls._table_name
    return model_name.lower()

def format_fts_table_name(cls):
    model_name = cls._related_model._table_name + "_fts"
    return model_name.lower()

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
        if engine == "sqlite3":
            settings = Settings.retrieve()
            d = SqliteDatabase(settings.db_path)
            cls.JSONField = SQLiteJSONField
        elif engine in ["mariadb", "mysql"]:
            d = MySQLDatabase("gws", user='gws', password='gencovery', host='mariadb', port=3306)
            cls.JSONField = MySQLJSONField
        else:
            raise Exception("gws.db.model.DbManager", "init", f"Db engine '{engine}' is not valid")
        
        cls.db.initialize(d)
        cls._engine = engine
        
DbManager.init("sqlite3")

# ####################################################################
#
# BaseModel class
#
# ####################################################################

class BaseModel(Base, Model):
    """
    Base class
    """
    
    JSONField = DbManager.JSONField
    
    _db_manager = DbManager
    _table_name = 'gws_base'

    @classmethod
    def is_sqlite3_engine(cls):
        return cls._db_manager._engine == "sqlite3"
    
    @classmethod
    def is_mysql_engine(cls):
        return cls._db_manager._engine in ["mysql", "mariadb"]
    
    def save(self, *args, **kwargs) -> bool:
        if not self.table_exists():
            self.create_table()
        
        return super().save(*args, **kwargs)
    
    class Meta:
        database = DbManager.db
        table_function = format_table_name

# ####################################################################
#
# BaseModel class
#
# ####################################################################

class BaseFTSModel(Base, FTS5Model):
    """
    Base class
    """

    rowid = RowIDField()
    title = SearchField()
    content = SearchField()
    
    _related_model = BaseModel
    
    def get_related(self, *args, **kwargs):
        t = self._related_model
        Q = t.select( *args, **kwargs ).where(t.id == self.rowid)
        return Q[0]
    
    def save(self, *args, **kwargs) -> bool:
        if not self.table_exists():
            self.create_table()
        
        return super().save(*args, **kwargs)
    
    class Meta:
        database = DbManager.db
        table_function = format_fts_table_name