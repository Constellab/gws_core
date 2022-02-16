

import importlib
import inspect
import os
from typing import Any, Dict, List

from ..core.utils.settings import ModuleInfo, Settings


class BrickHelper():
    @classmethod
    def get_all_bricks(cls) -> Dict[str, ModuleInfo]:
        """ Returns the info of all the bricks used by the Application """
        modules: Dict[str, ModuleInfo] = Settings.retrieve().get_modules()
        bricks: Dict[str, ModuleInfo] = {}
        for name, brick_info in modules.items():
            # skip app and skeleton 'bricks'
            if name == 'app' or name == 'skeleton':
                continue
            if brick_info.get("is_brick"):  # "brick" in brick_info["type"]:
                brick_info["name"] = name  # save the name in the object
                bricks[name] = brick_info
        return bricks

    @classmethod
    def get_brick_name(cls, obj: Any) -> str:
        """Methode to return a brick name of any object

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
    def get_brick_info(cls, obj: Any) -> ModuleInfo:
        """Methode to return a brick info of any object

        :param obj: class, method...
        :type obj: Any
        :rtype: str
        """
        brick_name = cls.get_brick_name(obj)

        bricks = cls.get_all_bricks()

        if brick_name not in bricks:
            raise Exception(f"Can't find the brick information of object ${obj}")

        return bricks[brick_name]

    @classmethod
    def get_brick_path(cls, obj: Any) -> str:
        """Methode to return a brick path of any object

        :param obj: class, method...
        :type obj: Any
        :rtype: str
        """
        name = cls.get_brick_name(obj)
        try:
            module = importlib.import_module(name)
        except Exception as err:
            raise Exception(f"Can't import python module {name}") from err
        return os.path.join(os.path.abspath(os.path.dirname(module.__file__)), "../../")
