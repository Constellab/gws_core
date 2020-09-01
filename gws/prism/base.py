# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import re
from peewee import SqliteDatabase, Model
from slugify import slugify as convert_to_slug

from gws.settings import Settings

def slugify(text, snakefy = False) -> str:
    """
    Returns the slugified text
    :param snakefy: Snakefy the text if True (i.e. uses undescores instead of dashes to separate text words), defaults to False
    :type snakefy: bool, optional
    :return: The slugified name
    :rtype: str
    """
    if slugify:
        text = convert_to_slug(text, to_lower=True, separator='-')
    elif snakefy:
        text = convert_to_slug(text, to_lower=True, separator='_')
    return text


def format_table_name(cls):
    model_name = cls._table_name
    return model_name.lower()


class DbManager:
    """
    DbManager class. Provides backend feature for managing databases. 
    """
    settings = Settings.retrieve()
    db = SqliteDatabase(settings.db_path)
    
    # @staticmethod
    # def create_tables(models: list, **options):
    #     """
    #     Creates the tables of a list of models. Wrapper of :meth:`DbManager.db.create_tables`
    #     :param models: List of model instances
    #     :type models: list
    #     :param options: Extra parameters passed to :meth:`DbManager.db.create_tables`
    #     :type options: dict, optional
    #     """
    #     DbManager.db.create_tables(models, **options)

    # @staticmethod
    # def drop_tables(models: list, **options):
    #     """
    #     Drops the tables of a list of models. Wrapper of :meth:`DbManager.db.drop_tables`
    #     :param models: List of model instances
    #     :type models: list
    #     :param options: Extra parameters passed to :meth:`DbManager.db.create_tables`
    #     :type options: dict, optional
    #     """
    #     DbManager.db.drop_tables(models, **options)

    # @staticmethod
    # def connect_db() -> bool:
    #     """
    #     Open a connection to the database. Reuse existing open connection if any. 
    #     Wrapper of :meth:`DbManager.db.connect`
    #     :return: True if the connection successfully opened, False otherwise
    #     :rtype: bool
    #     """
    #     return DbManager.db.connect(reuse_if_open=True)
    
    # @staticmethod
    # def close_db() -> bool:
    #     """
    #     Close the connection to the database. Wrapper of :meth:`DbManager.db.close`
    #     :return: True if the connection successfully closed, False otherwise
    #     :rtype: bool
    #     """
    #     return DbManager.db.close()

    # @staticmethod
    # def get_tables(schema=None) -> list:
    #     """
    #     Get the list of tables. Wrapper of :meth:`DbManager.db.get_tables`
    #     :return: The list of the tables
    #     :rtype: list
    #     """
    #     return DbManager.db.get_tables(schema)

class Base(Model):
    """
    Base class
    """

    _table_name = 'base'

    def classname(self, slugify = False, snakefy = False, replace_uppercase = False) -> str:
        """
        Returns the name the class
        :param slugify: Slugify the returned class name if True, defaults to False
        :type slugify: bool, optional
        :param snakefy: Snakefy the returned class name if True, defaults to False
        :type snakefy: bool, optional
        :param replace_uppercase: Replace upper cases by "-" if True, defaults to False
        :type replace_uppercase: bool, optional
        :return: The class name
        :rtype: str
        """
        name = type(self).__name__
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

    def property_names(self, instance = None) -> list:
        """
        Returns the property names
        :return: The list of the properties
        :rtype: list
        """
        cls = type(self)
        property_names = []
        m = inspect.getmembers(cls)
        for i in m:
            if not instance is None:
                if isinstance(i[1], instance):
                    property_names.append(i[0])
            elif not i[0].startswith('_') and not inspect.isfunction(i[1]) and not inspect.ismethod(i[1]) and not inspect.isclass(i[1]):
                property_names.append(i[0])

        return property_names
    
    def method_names(self):
        cls = type(self)
        method_names = []
        m = inspect.getmembers(cls)
        for i in m:
            if not i[0].startswith('_') and inspect.isfunction(i[1]) and inspect.ismethod(i[1]):
                method_names.append(i[0])

        return method_names

    class Meta:
        database = DbManager.db
        table_function = format_table_name