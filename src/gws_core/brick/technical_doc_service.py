# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
from typing import Any, Dict, List, Type

from gws_core.protocol.protocol_typing import ProtocolTyping

from ..core.utils.reflector_helper import ReflectorHelper
from ..model.typing import Typing
from ..resource.resource import Resource
from ..resource.resource_typing import ResourceTyping
from ..resource.view.view_helper import ViewHelper
from ..resource.view.view_meta_data import ResourceViewMetaData
from ..task.task_typing import TaskTyping
from .brick_helper import BrickHelper


class TechnicalDocService():

    @classmethod
    def generate_technical_doc(cls, brick_name: str) -> dict:
        """Method to return the technical doc information about a brick to upload it on the hub
        """

        brick_info = BrickHelper.get_brick_info_and_check(brick_name)

        return {
            "json_version": 1,
            "brick_name": brick_info["name"],
            "brick_version": brick_info["version"],
            "resources": cls.export_typing_technical_doc(brick_name, ResourceTyping),
            "tasks": cls.export_typing_technical_doc(brick_name, TaskTyping),
            "protocols": cls.export_typing_technical_doc(brick_name, ProtocolTyping),
        }

    @classmethod
    def export_typing_technical_doc(cls, brick_name: str, typing_class: Type[Typing]) -> list:
        typings: List[Typing] = typing_class.get_by_brick_and_object_type(brick_name)
        sorted_typings = sorted(typings, key=lambda x: len(x.get_ancestors()))
        json_list = []
        for typing in sorted_typings:
            json_ = cls._get_typing_technical_doc(typing)

            if json_ is None:
                continue

            json_list.append(json_)
        return json_list

    # TODO TO FIX
    @classmethod
    def _get_typing_technical_doc(cls, typing: Typing) -> dict:
        type_: Type[Resource] = typing.get_type()
        if type_ is None:
            return None
        res = typing.to_json(deep=True)
        if type(typing) is ResourceTyping:
            res["methods"] = cls.get_class_methods_docs(type_)
        return res

    @classmethod
    def get_class_methods_docs(cls, type_: type) -> List[Dict[str, Any]]:
        if not inspect.isclass(type_):
            return None
        methods: Any = inspect.getmembers(type_, predicate=inspect.isfunction)
        views_methods: List[ResourceViewMetaData] = ViewHelper.get_views_of_resource_type(type_)
        views_methods_json: List[dict] = [m.to_complete_json() for m in views_methods]
        func_methods: Any = [method for method in methods if not ReflectorHelper.is_decorated_with_view(method)]
        public_func_methods: Any = [(m[0], m[1])
                                    for m in func_methods if not m[0].startswith('_') or m[0] == '__init__']
        funcs: List[Dict[str, Any]] = ReflectorHelper.get_methods_doc(public_func_methods)
        return {
            'funcs': funcs if len(funcs) > 0 else None,
            'views': views_methods_json if len(views_methods_json) > 0 else None
        }
