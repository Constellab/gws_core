# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import re

from contextvars import ContextVar
from peewee import SqliteDatabase, Model, _ConnectionState as _PeeweeConnectionState
from playhouse.sqlite_ext import JSONField, RowIDField, SearchField, FTS5Model

from slugify import slugify as _slugify
from gws.settings import Settings
from gws.base import Base

# ####################################################################
#
# DbManager class
#
# ####################################################################

def format_table_name(cls):
    model_name = cls._table_name
    return model_name.lower()

def format_fts_table_name(cls):
    model_name = cls._related_model._table_name + "_fts"
    return model_name.lower()

db_state_default = {"closed": None, "conn": None, "ctx": None, "transactions": None}
db_state = ContextVar("db_state", default=db_state_default.copy())

class PeeweeConnectionState(_PeeweeConnectionState):
    def __init__(self, **kwargs):
        super().__setattr__("_state", db_state)
        super().__init__(**kwargs)

    def __setattr__(self, name, value):
        self._state.get()[name] = value

    def __getattr__(self, name):
        return self._state.get()[name]

class DbManager:
    """
    DbManager class. Provides backend feature for managing databases. 
    """
    settings = Settings.retrieve()
    db = SqliteDatabase(settings.db_path, check_same_thread=False)
    db._state = PeeweeConnectionState()
    
# ####################################################################
#
# BaseModel class
#
# ####################################################################

class BaseModel(Base, Model):
    """
    Base class
    """

    _table_name = 'gws_base'
    
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
        # Use the porter stemming algorithm to tokenize content.
        #options = {'tokenize': 'porter'}
        #options = {'content': Base.data}
