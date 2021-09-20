# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import importlib
import inspect
import os
import random
import re
import string
import uuid
from typing import Any, Dict, List, Tuple, Type

from slugify import slugify as _slugify


class Utils:

    # -- G --
    @staticmethod
    def generate_random_chars(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits) -> str:
        return ''.join(random.choice(chars) for _ in range(size))

    @staticmethod
    def get_brick_name(obj: Any) -> str:
        """Methode to return a brick of any object

        :param obj: class, method...
        :type obj: Any
        :rtype: str
        """
        module = inspect.getmodule(obj)
        if module is None:
            raise Exception(f"Can't find python module of object {obj}")
        modules: List[str] = module.__name__.split('.')
        return modules[0]

    @classmethod
    def get_all_brick_names(cls) -> List[str]:
        """ Returns the names of all the bricks used by the Application """
        from ..utils.settings import Settings
        settings = Settings.retrieve()
        brick_names: List[str] = []
        for name, data in settings.data["modules"].items():
            if "brick" in data["type"]:
                brick_names.append(name)
        return brick_names

        # from ...core.model.base import Base
        # if not getattr(cls,'__brick_names', None):
        #     subclasses: List[Type[Base]] = Base.inheritors()
        #     cls.__brick_names: List[str] = []
        #     for subclass in subclasses:
        #         top_pkg = subclass.module_name().split('.')[0]
        #         if top_pkg not in cls.__brick_names:
        #             cls.__brick_names.append(top_pkg)
        # return cls.__brick_names

    @staticmethod
    def get_brick_path(obj: Any) -> str:
        name = Utils.get_brick_name(obj)
        try:
            module = importlib.import_module(name)
        except Exception as err:
            raise Exception(f"Can't import python module {name}") from err
        return os.path.join(os.path.abspath(os.path.dirname(module.__file__)), "../../")

    @classmethod
    def get_all_brick_paths(cls) -> List[str]:
        """ Returns all the paths of all the brick used by the Application """
        from ..utils.settings import Settings
        settings = Settings.retrieve()
        brick_paths: List[str] = []
        for _, data in settings.data["modules"].items():
            if "brick" in data["type"]:
                brick_paths.append(data["path"])
        return brick_paths

        # if not getattr(cls,'__brick_paths', None):
        #     cls.__brick_paths = []
        #     brick_names = Utils.get_all_brick_names()
        #     for name in brick_names:
        #         module = importlib.import_module(name)
        #         p = os.path.abspath(os.path.dirname(module.__file__))
        #         cls.__brick_paths.append(p)
        # return cls.__brick_paths

    # -- I --

    @staticmethod
    def import_all_modules():
        brick_paths: List[str] = Utils.get_all_brick_paths()
        for path in brick_paths:
            _, files = Utils.walk_dir(os.path.join(path, "src"))
            for py_file in files:
                parts = py_file.split("/src/")[-1].split("/")
                parts[-1] = os.path.splitext(parts[-1])[0]  # remove .py extension
                module_name = ".".join(parts)
                try:
                    importlib.import_module(module_name)
                except Exception as err:
                    raise Exception(f"Cannot import module {module_name}.") from err

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
    def walk_dir(path):
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
    def get_model_type(cls, type_str: str = None) -> Type[Any]:
        """
        Get the type of a registered model using its litteral type

        :param type: Litteral type (can be a slugyfied string)
        :type type: str
        :return: The type if the model is registered, None otherwise
        :type: `str`
        """

        if type_str is None:
            return None

        tab = type_str.split(".")
        length = len(tab)
        module_name = ".".join(tab[0:length-1])
        function_name = tab[length-1]
        module = importlib.import_module(module_name)
        return getattr(module, function_name, None)

    @classmethod
    def generate_uuid(cls) -> str:
        return str(uuid.uuid4())

    @classmethod
    def get_property_names_with_type(cls, class_type: type, type_: type) -> Dict[str, Any]:
        properties: Dict[str, Any] = {}
        member_list: List[Tuple[str, Any]] = inspect.getmembers(class_type)

        for member in member_list:
            member_value = member[1]
            if not inspect.isfunction(member_value) and \
                not inspect.ismethod(member_value) and \
                not inspect.isclass(member_value) and \
                    isinstance(member_value, type_):

                properties[member[0]] = member[1]

        return properties
