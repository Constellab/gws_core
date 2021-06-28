# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union
import inspect
import re
from gws.utils import slugify as slug

class Base:
    """
    Base class
    """
    
    @classmethod
    def classname(cls, slugify: bool = False, snakefy: bool = False, replace_uppercase: bool = False) -> str:
        """
        Returns the name of the class

        :param slugify: True to slugify the class name if True, defaults to False
        :type slugify: bool, optional
        :param snakefy: True to snakefy the class name if True, defaults to False
        :type snakefy: bool, optional
        :param replace_uppercase: Replace upper cases by "-" if True, defaults to False
        :type replace_uppercase: bool, optional
        :return: The class name
        :rtype: `str`
        """

        name = cls.__name__
        if replace_uppercase:
            name = re.sub('([A-Z]{1})', r'-\1', name)
            name = name.strip("-")

        if slugify:
            name = slug(name, to_lower=True, snakefy=True)
        elif snakefy:
            name = slug(name, to_lower=True, snakefy=True)
        return name
    
    @classmethod
    def full_classname(cls, slugify:bool = False, snakefy:bool = False) -> str:
        """
        Returns the full name of the class

        :param slugify: Slugify the returned class name if True, defaults to False
        :type slugify: bool, optional
        :param snakefy: Snakefy the returned class name if True, defaults to False
        :type snakefy: `bool`
        :return: The class name
        :rtype: `str`
        """

        module = inspect.getmodule(cls).__name__
        name = cls.__name__
        full_name = module + "." + name

        if slugify:
            full_name = slug(full_name, to_lower=True, snakefy=False)
        elif snakefy:
            full_name = slug(full_name, to_lower=True, snakefy=True)
        
        return full_name

    @classmethod
    def module(cls) -> str:
        """
        Returns the module name of the class

        :return: The module name of the class
        :rtype: `str`
        """

        module = inspect.getmodule(cls).__name__
        return module

    @classmethod
    def property_names(cls, instance:(type, Union[type],)=None, exclude:(type, Union[type],)=None) -> List[str]:
        """
        Retrieves the property names

        :param instance: The types of the properties to retrieve. Set `None` to retrieve all.
        :type instance: `type` or `Union[type]`
        :return: The types of the properties to exclude. Set `None` to exclude nothing.
        :rtype: `type`, `Union[type]`
        :return: The list of the properties
        :rtype: `List[str]`
        """

        property_names = []
        member_list = inspect.getmembers(cls)
        for member in member_list:
            if not instance is None:
                if not exclude is None:
                    if isinstance(member[1], instance) and not isinstance(member[1], exclude):
                        property_names.append(member[0])
                else:
                    if isinstance(member[1], instance):
                        property_names.append(member[0])
                        
            elif not member[0].startswith('_')     and \
                 not inspect.isfunction(member[1]) and \
                 not inspect.ismethod(member[1])   and \
                 not inspect.isclass(member[1]):

                property_names.append(member[0])

        return property_names

    @classmethod
    def method_names(cls) -> List[str]:
        """
        Returns the list of the methods

        :return: The lsit of methods
        :rtype: `List[str]`
        """

        method_names = []
        members = inspect.getmembers(cls)
        for member in members:
            if not member[0].startswith('_') and \
               inspect.isfunction(member[1]) and \
               inspect.ismethod(member[1]):
                
                method_names.append(member[0])

        return method_names

