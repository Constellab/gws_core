# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import os
import random
import string
import importlib
from typing import Any, List, Type

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from slugify import slugify as _slugify


class Utils:

    # -- G --
    @staticmethod
    def generate_random_chars(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits) -> str:
        return ''.join(random.choice(chars) for _ in range(size))

    # -- S --

    @staticmethod
    def slugify(text: str, snakefy: bool = False, to_lower: bool = True) -> str:
        """
        Returns the slugified text

        :param text: Text to slugify
        :type text: `str`
        :param snakefy: Snakefy the text if True (i.e. uses undescores instead of dashes to separate text words), defaults to False
        :type snakefy: `bool`
        :param to_lower: True to lower all characters, False otherwise
        :type to_lower: `bool`
        :return: The slugified text
        :rtype: str
        """

        if snakefy:
            text = _slugify(text, to_lower=to_lower, separator="_")
        else:
            text = _slugify(text, to_lower=to_lower, separator='-')

        return text

    # -- S --
    @staticmethod
    def sort_dict_by_key(json_dict):
        if not json_dict:
            return json_dict

        return {k: Utils.sort_dict_by_key(v) if isinstance(v, json_dict) else v
                for k, v in sorted(json_dict.items())}

    # -- T --
    @staticmethod
    def to_camel_case(snake_str: str, capitalize_first: bool = False):
        components = snake_str.split('_')
        c0 = components[0].title() if capitalize_first else components[0]
        return c0 + ''.join(x.title() for x in components[1:])

    @staticmethod
    def get_brick_name(obj: Any) -> str:
        """Methode to return a brick of any object

        :param obj: class, method...
        :type obj: Any
        :rtype: str
        """
        module = inspect.getmodule(obj)
        if module is None:
            raise BadRequestException(
                f"Can't find python module of object {obj}")
        modules: List[str] = module.__name__.split('.')
        return modules[0]

    @classmethod
    def get_all_brick_names(cls) -> List[str]:
        """ Returns the names of all the bricks used by the Application """
        from ...core.model.base import Base
        if not getattr(cls,'__brick_names', None):
            subclasses: List[Type[Base]] = Base.inheritors()
            cls.__brick_names: List[str] = []
            for subclass in subclasses:
                top_pkg = subclass.module_name().split('.')[0]
                if top_pkg not in cls.__brick_names:
                    cls.__brick_names.append(top_pkg)
        return cls.__brick_names

    @staticmethod
    def get_brick_path(obj: Any) -> str:
        name = Utils.get_brick_name(obj)
        try:
            module = importlib.import_module(name)
        except Exception as err:
            raise BadRequestException(
                f"Can't import python module {name}") from err
        return os.path.abspath(os.path.dirname(module.__file__))

    @classmethod
    def get_all_brick_paths(cls) -> List[str]:
        """ Returns all the paths of all the brick used by the Application """
        if not getattr(cls,'__brick_paths', None):
            cls.__brick_paths = []
            brick_names = Utils.get_all_brick_names()
            for name in brick_names:
                module = importlib.import_module(name)
                p = os.path.abspath(os.path.dirname(module.__file__))
                cls.__brick_paths.append(p)
        return cls.__brick_paths
