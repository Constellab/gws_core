# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import re
from typing import List, Type

from ..utils.string_helper import StringHelper


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
            name = StringHelper.slugify(name, to_lower=True, snakefy=True)
        elif snakefy:
            name = StringHelper.slugify(name, to_lower=True, snakefy=True)
        return name

    @classmethod
    def full_classname(cls, slugify: bool = False, snakefy: bool = False) -> str:
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
            full_name = StringHelper.slugify(full_name, to_lower=True, snakefy=False)
        elif snakefy:
            full_name = StringHelper.slugify(full_name, to_lower=True, snakefy=True)

        return full_name

    @classmethod
    def inheritors(cls) -> List[Type['Base']]:
        """ Get all the classes that inherit this class """
        return set(cls.__subclasses__()).union(
            [s for c in cls.__subclasses__() for s in c.inheritors()])

    @classmethod
    def module_name(cls) -> str:
        """
        Returns the module name of the class

        :return: The module name of the class
        :rtype: `str`
        """

        module = inspect.getmodule(cls).__name__
        return module

    @classmethod
    def property_names(cls, instance: type = None, exclude: type = None) -> List[str]:
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

            elif not member[0].startswith('_') and \
                    not inspect.isfunction(member[1]) and \
                    not inspect.ismethod(member[1]) and \
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

    @classmethod
    def property_method_names(cls):
        return cls.decorated_method_names(decorator_name="property")

    @classmethod
    def decorated_method_names(cls, decorator_name):
        return list(cls.__decorated_method_names(decorator_name))

    @classmethod
    def __decorated_method_names(cls, decorator_name):
        sourcelines = inspect.getsourcelines(cls)[0]
        for i, line in enumerate(sourcelines):
            line = line.strip()
            if line.split('(')[0].strip() == '@' + decorator_name:  # leaving a bit out
                next_line = sourcelines[i + 1]
                name = next_line.split('def')[1].split('(')[0].strip()
                if name:
                    yield(name)
