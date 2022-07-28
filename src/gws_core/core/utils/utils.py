# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import inspect
import os
import re
from importlib import import_module
from importlib.util import find_spec
from json import dumps
from typing import Any, List, Optional, Set, Tuple, Type, Union, get_args


class Utils:

    @staticmethod
    def sort_dict_by_key(json_dict):
        if not json_dict:
            return json_dict

        return {k: Utils.sort_dict_by_key(v) if isinstance(v, json_dict) else v
                for k, v in sorted(json_dict.items())}

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
    def json_are_equals(json1: Any, json2: Any) -> bool:
        """Check if two json are equals
        """
        return dumps(json1, sort_keys=True) == dumps(json2, sort_keys=True)

    @staticmethod
    def rename_duplicate_in_str_list(list_: List[str]) -> List[str]:
        """Rename all duplicated element in a list of str with _1, _2... at the end
        """
        new_list = []

        for item in list_:
            if item not in new_list:
                new_list.append(item)
                continue

            i = 1
            while f"{item}_{i}" in new_list:
                i += 1

            new_list.append(f"{item}_{i}")

        return new_list
