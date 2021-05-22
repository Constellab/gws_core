# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import re
from gws.settings import Settings
from gws.utils import slugify as slug

class Base:
    """
    Base class
    """
    
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
            name = slug(name, to_lower=True, separator='-')
        elif snakefy:
            name = slug(name, to_lower=True, separator='_')
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
            full_name = slug(full_name, to_lower=True, separator='-')
        elif snakefy:
            full_name = slug(full_name, to_lower=True, separator='_')
        
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

