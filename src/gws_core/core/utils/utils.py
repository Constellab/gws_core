# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import inspect
import os
import random
import re
import string
import uuid
from importlib import import_module
from importlib.util import find_spec
from json import dumps
from typing import Any, List, Optional, Set, Tuple, Type, Union, get_args

from slugify import slugify as _slugify


class Utils:

    # -- G --
    @staticmethod
    def generate_random_chars(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits) -> str:
        return ''.join(random.choice(chars) for _ in range(size))

    @classmethod
    def get_notebook_paths(cls) -> str:
        """ Returns all the paths of all the brick used by the Application """
        from ..utils.settings import Settings
        settings = Settings.retrieve()
        return settings.data["modules"]["notebook"]["path"]

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

    # -- W --

    @staticmethod
    def walk_dir(path) -> Tuple[List[str], List[str]]:
        dirs = []
        files = []
        reg = re.compile(r"^[a-zA-Z].*\.py$")

        def is_valid_dir(d) -> bool:
            return not d.startswith("_") and not "/_" in d

        for root, subdirs, subfiles in os.walk(path):
            subdirs[:] = [d for d in subdirs if is_valid_dir(d)]

            # gather dirs
            for f in subfiles:
                if reg.match(f):
                    files = [*files, os.path.join(root, f)]

            dirs = [*dirs, root]
        return dirs, files

    @classmethod
    def get_model_type(cls, type_str: str = None) -> Optional[Type[Any]]:
        """
        Get the type of a registered model using its litteral type

        :param type: Litteral type (can be a slugyfied string)
        :type type: str
        :return: The type if the model is registered, None otherwise
        :type: `str`
        """

        if type_str is None:
            return None

        try:
            tab = type_str.split(".")
            length = len(tab)
            module_name = ".".join(tab[0:length-1])
            function_name = tab[length-1]

            if find_spec(module_name) is None:
                return None

            module = import_module(module_name)

            return getattr(module, function_name, None)
        except:
            return None

    @classmethod
    def model_type_exists(cls, type_str: str = None) -> bool:
        return cls.get_model_type(type_str) is not None

    @classmethod
    def generate_uuid(cls) -> str:
        return str(uuid.uuid4())

    @staticmethod
    def issubclass(__cls: type, __class_or_tuple:  Union[type, Tuple[Union[type, Tuple[Any, ...]], ...]]) -> bool:
        """issubclass safe that check the input is a class and avoid exception
        """
        return inspect.isclass(__cls) and issubclass(__cls, __class_or_tuple)

    @staticmethod
    def value_is_in_literal(value: Any, literal_type: Type) -> bool:
        """Check wheter a value in in a listeral list
        """
        return value in Utils.get_literal_values(literal_type)

    @staticmethod
    def get_literal_values(literal_type: Type) -> Tuple[Any]:
        """Return the list of literal values
        """
        return list(get_args(literal_type))

    @staticmethod
    def get_all_subclasses(class_: Type) -> Set[Type]:
        """Return all the subclasses type of a class, it does not include the main class

        :param class_: class to retrieve the subclasses
        :type class_: Type
        :return: _description_
        :rtype: Set[Type]
        """

        return set(class_.__subclasses__()).union(
            [s for c in class_.__subclasses__() for s in Utils.get_all_subclasses(c)])

    @staticmethod
    def get_parent_classes(class_: Type, max_parent: Type = None) -> List[Type]:
        """Return  a list of parent class of class_ arg (containing class_).
        :param class_: [description]
        :type class_: Type
        :param max_parent: if provided, doesn't return parent of max_parent class, defaults to None
        :type max_parent: Type, optional
        :return: [description]
        :rtype: List[Type]
        """
        mro: List[Type] = inspect.getmro(class_)
        parents: List[Type] = []
        for parent_type in mro:
            if max_parent is None or issubclass(parent_type, max_parent):
                parents.append(parent_type)
        return parents

    @staticmethod
    def camel_case_to_sentence(name: str) -> str:
        """Convert a camel case to sentence like
        Ex 'TestClass2Build' -> 'Test class2 build'

        :param name: [description]
        :type name: str
        :return: [description]
        :rtype: str
        """
        if name is None:
            return None
        name = name.replace(' ', '')
        name = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1 \2', name).capitalize()

    @staticmethod
    def snake_case_to_sentence(name: str) -> str:
        """Convert a snake case to sentence like
        Ex 'test_class2_build' -> 'Test class2 build'
        """
        if name is None:
            return None
        name = name.lower().replace(' ', '').replace('_', ' ')
        return name.capitalize()

    @staticmethod
    def str_to_enum(enum_class: Type, str_value: str) -> Any:
        """Convert a string to an enum value
        """
        return enum_class(str_value)

    @staticmethod
    def json_are_equals(json1: Any, json2: Any) -> bool:
        """Check if two json are equals
        """
        return dumps(json1, sort_keys=True) == dumps(json2, sort_keys=True)

    @staticmethod
    def str_is_alphanumeric(str_: str) -> bool:
        """Check if a string is alphanumeric with underscore"""
        if str_ is None:
            return False

        return bool(re.match("^[a-zA-Z0-9_]+$", str_))

    @staticmethod
    def str_remove_whitespaces(str_: str) -> str:
        """Remove all whitespace of a string"""
        if str_ is None:
            return None

        pattern = re.compile(r'\s+')
        return re.sub(pattern, '', str_)
