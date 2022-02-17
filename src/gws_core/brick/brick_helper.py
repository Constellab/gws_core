

import inspect
from typing import Any, Dict, List, TypedDict

from ..core.utils.settings import ModuleInfo, Settings


class BrickVersion(TypedDict):
    name: str
    version: str
    repo_type: str
    repo_commit: str


class LabConfig(TypedDict):
    """Object representing the complete config of a lab to recreate it
    """
    version: int  # version of the config
    brick_versions: List[BrickVersion]


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
        """Methode to return a brick.
        If object, retrieve the brick of the object
        If string, retrieve the brick of name

        :param obj: class, method...
        :type obj: Any
        :rtype: str
        """

        if isinstance(obj, str):
            brick_name = obj
        else:
            brick_name = cls.get_brick_name(obj)

        bricks = cls.get_all_bricks()

        if brick_name not in bricks:
            raise Exception(f"Can't find the brick information of object ${obj}")

        return bricks[brick_name]

    @classmethod
    def get_lab_config(cls) -> LabConfig:
        """Get the config of the lab to rebuild one as a copy of this one

        :return: _description_
        :rtype: List[BrickVersion]
        """
        bricks = cls.get_all_bricks()

        brick_versions: List[BrickVersion] = []

        for brick in bricks.values():
            # ignore app brick
            if brick['repo_type'] == 'app':
                continue

            brick_versions.append({
                'name': brick['name'],
                'version': brick['version'],
                'repo_type': brick['repo_type'],
                'repo_commit': brick['repo_commit']
            })
        return {
            'version': 1,
            'brick_versions': brick_versions
        }
