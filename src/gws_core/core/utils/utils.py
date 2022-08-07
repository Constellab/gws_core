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

from numpy import double


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
            new_list.append(Utils.generate_unique_str_for_list(new_list, item))

        return new_list

    @staticmethod
    def generate_unique_str_for_list(list_: List[str], str_: str) -> str:
        """Generate a unique str for a list of str.
        Append _1, _2... at the end if the str is already in the list
        """
        if str_ not in list_:
            return str_

        i = 1
        while f"{str_}_{i}" in list_:
            i += 1

        return f"{str_}_{i}"

    @staticmethod
    def is_primitive(obj: Any) -> bool:
        """Check if an object is a primitive type
        """
        return obj is None or type(obj) in (int, float, str, bool, double)

    @staticmethod
    def is_json(obj: Any) -> bool:
        """Check if an object is a json. Ok is type is primitive or a list or a dict containing
        list dict or primitive...
        """
        if Utils.is_primitive(obj):
            return True

        if isinstance(obj, list):
            for item in obj:
                if not Utils.is_json(item):
                    return False
            return True

        if isinstance(obj, dict):
            for key, value in obj.items():
                if not Utils.is_primitive(key) or not Utils.is_json(value):
                    return False
            return True

        return False

    @staticmethod
    def json_equals(json_1: Union[dict, list], json_2: Union[dict, list], ignore_keys: List[str] = None) -> bool:
        """Assert a json with possibility to ignore key
        """
        return Utils._json_equals_recur(json_1, json_2, ignore_keys, "") is None

    @staticmethod
    def assert_json_equals(json_1: Union[dict, list], json_2: Union[dict, list], ignore_keys: List[str] = None):
        """Assert a json with possibility to ignore key
        """
        result = Utils._json_equals_recur(json_1, json_2, ignore_keys, "")

        if result is None:
            return None

        raise AssertionError(result)

    @staticmethod
    def _json_equals_recur(
            json_1: Union[dict, list],
            json_2: Union[dict, list],
            ignore_keys: List[str] = None,
            cumulated_key: str = "") -> Optional[str]:

        # handle list
        if isinstance(json_1, list):
            if not isinstance(json_2, list):
                return f"The second object is not a list for key '{cumulated_key}'."

            if len(json_1) != len(json_2):
                return f"Length of array different for key '{cumulated_key}'."

            for index, value in enumerate(json_1):
                result = Utils._json_equals_recur(value, json_2[index], ignore_keys, f"{cumulated_key}[{index}]")

                if result is not None:
                    return result

            return None

        # Handle dict
        if isinstance(json_1, dict):
            if not isinstance(json_1, dict):
                return f"The seconde object is not a dict for key '{cumulated_key}'."

            if len(json_1) != len(json_2):
                return f"Length of object different for key '{cumulated_key}'."

            for key, value in json_1.items():
                if ignore_keys and key in ignore_keys:
                    continue

                result = Utils._json_equals_recur(value, json_2[key], ignore_keys, f"{cumulated_key}.{key}")
                if result is not None:
                    return result

            return None

        # Handle primitive value
        if json_1 != json_2:
            return f"Values differents for key '{cumulated_key}'. First: '{json_1}'. Second: '{json_2}'"

        return None
