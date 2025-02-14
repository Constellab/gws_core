

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
