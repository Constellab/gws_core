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

def slugify(text: str, snakefy: bool = False) -> str:
    """
    Returns the slugified text

    :param snakefy: Snakefy the text if True (i.e. uses undescores instead of dashes to separate text words), defaults to False
    :type snakefy: bool, optional
    :return: The slugified name
    :rtype: str
    """
    
    if snakefy:
        text = _slugify(text, to_lower=True, separator='_')
    else:
        text = _slugify(text, to_lower=True, separator='-')
        
    return text

# ####################################################################
#
# Base class
#
# ####################################################################


class Base:

    @classmethod
    def classname(cls, slugify: bool = False, snakefy: bool = False, replace_uppercase: bool = False) -> str:
        """
        Returns the name of the class

        :param slugify: Slugify the returned class name if True, defaults to False
        :type slugify: bool, optional
        :param snakefy: Snakefy the returned class name if True, defaults to False
        :type snakefy: bool, optional
        :param replace_uppercase: Replace upper cases by "-" if True, defaults to False
        :type replace_uppercase: bool, optional
        :return: The class name
        :rtype: str
        """
        name = cls.__name__
        if replace_uppercase:
            name = re.sub('([A-Z]{1})', r'-\1', name)
            name = name.strip("-")

        if slugify:
            name = convert_to_slug(name, to_lower=True, separator='-')
        elif snakefy:
            name = convert_to_slug(name, to_lower=True, separator='_')
        return name
    
    @classmethod
    def full_classname(cls, slugify = False, snakefy = False):
        """
        Returns the full name of the class

        :param slugify: Slugify the returned class name if True, defaults to False
        :type slugify: bool, optional
        :param snakefy: Snakefy the returned class name if True, defaults to False
        :type snakefy: bool, optional
        :return: The class name
        :rtype: str
        """
        module = inspect.getmodule(cls).__name__
        name = cls.__name__
        full_name = module + "." + name

        if slugify:
            full_name = convert_to_slug(full_name, to_lower=True, separator='-')
        elif snakefy:
            full_name = convert_to_slug(full_name, to_lower=True, separator='_')
        
        return full_name

    @classmethod
    def module(cls) -> str:
        """
        Returns the module of the class

        :return: The module
        :rtype: str
        """
        module = inspect.getmodule(cls).__name__
        return module

    @classmethod
    def property_names(cls, instance=None, exclude=None) -> list:
        """
        Returns the property names

        :return: The list of the properties
        :rtype: list
        """
        property_names = []
        m = inspect.getmembers(cls)
        for i in m:
            if not instance is None:
                if not exclude is None:
                    if isinstance(i[1], instance) and not isinstance(i[1], exclude):
                        property_names.append(i[0])
                else:
                    if isinstance(i[1], instance):
                        property_names.append(i[0])
                        
            elif not i[0].startswith('_') and not inspect.isfunction(i[1]) and not inspect.ismethod(i[1]) and not inspect.isclass(i[1]):
                property_names.append(i[0])

        return property_names
    
    @classmethod
    def method_names(cls):
        method_names = []
        m = inspect.getmembers(cls)
        for i in m:
            if not i[0].startswith('_') and inspect.isfunction(i[1]) and inspect.ismethod(i[1]):
                method_names.append(i[0])

        return method_names

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
    
    def get_related(self):
        return self._related_model.get_by_id(self.rowid)

    class Meta:
        database = DbManager.db
        table_function = format_fts_table_name
        # Use the porter stemming algorithm to tokenize content.
        #options = {'tokenize': 'porter'}
        #options = {'content': Base.data}
