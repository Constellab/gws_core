# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
from typing import Any, Dict, List, Optional

from gws_core.core.db.version import Version

from ..core.utils.settings import Settings
from .brick_dto import BrickInfo, BrickVersion


class BrickHelper():
    @classmethod
    def get_all_bricks(cls) -> Dict[str, BrickInfo]:
        """ Returns the info of all the bricks used by the Application """
        return Settings.get_instance().get_bricks()

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
    def get_brick_info(cls, obj: Any) -> Optional[BrickInfo]:
        """Methode to return a brick.
        If object, retrieve the brick of the object
        If string, retrieve the brick of name

        Return None if not found

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
            # secific case for the test mode when brick name is test filename
            if Settings.get_instance().is_test:
                return {
                    "path": '',
                    "name": brick_name,
                    "version": '0.0.0',
                    "repo_commit": '',
                    "repo_type": 'git',
                    "parent_name": None,
                    "error": None,
                }
            return None

        return bricks[brick_name]

    @classmethod
    def get_brick_info_and_check(cls, obj: Any) -> BrickInfo:
        """Methode to return a brick.
        If object, retrieve the brick of the object
        If string, retrieve the brick of name

        Raise Exception if not found

        :param obj: class, method...
        :type obj: Any
        :rtype: str
        """

        brick_info = cls.get_brick_info(obj)

        if brick_info is None:
            raise Exception(
                f"Can't find the brick information of object '{obj}'")

        return brick_info

    @classmethod
    def get_brick_version(cls, obj: Any) -> Version:
        """Methode to return a brick version of any object
           If object, retrieve the brick of the object
           If string, retrieve the brick of name
        """

        brick_info = cls.get_brick_info_and_check(obj)
        return Version(brick_info.get("version"))

    @classmethod
    def get_all_brick_versions(cls) -> List[BrickVersion]:
        bricks = cls.get_all_bricks()
        brick_versions: List[BrickVersion] = []

        for brick in bricks.values():
            # ignore app brick
            if brick['repo_type'] == 'app':
                continue

            brick_versions.append({
                'name': brick['name'],
                'version': brick['version'],
            })
        return brick_versions

    @classmethod
    def brick_is_loaded(cls, brick_name: str) -> bool:
        return brick_name in cls.get_all_bricks()
