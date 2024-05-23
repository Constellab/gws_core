

from typing import List, Type

from gws_core.brick.technical_doc_dto import TechnicalDocDTO
from gws_core.model.typing_dto import TypingFullDTO
from gws_core.protocol.protocol_typing import ProtocolTyping

from ..model.typing import Typing
from ..resource.resource import Resource
from ..resource.resource_typing import ResourceTyping
from ..task.task_typing import TaskTyping
from .brick_helper import BrickHelper

import sys, inspect


class TechnicalDocService():

    @classmethod
    def generate_technical_doc(cls, brick_name: str) -> TechnicalDocDTO:
        """Method to return the technical doc information about a brick to upload it on the hub
        """

        brick_info = BrickHelper.get_brick_info_and_check(brick_name)

        resources = cls.export_typing_technical_doc(brick_name, ResourceTyping)
        tasks = cls.export_typing_technical_doc(brick_name, TaskTyping)
        protocols = cls.export_typing_technical_doc(brick_name, ProtocolTyping)

        # Get all the classes of the brick except the resources, tasks and protocols
        rtp = resources + tasks + protocols
        other_classes = {}
        clsmembers = inspect.getmembers(sys.modules[brick_name], inspect.isclass)
        for name, obj in clsmembers:
            ok = True
            for t in rtp:
                if name == t.unique_name:
                    ok = False
                    break
            if ok:
                doc = cls._get_non_typing_obj_technical_doc(obj)
                other_classes[name] = doc

        return TechnicalDocDTO(
            json_version=1,
            brick_name=brick_info["name"],
            brick_version=brick_info["version"],
            resources= resources,
            tasks=tasks,
            protocols=protocols,
            other_classes=other_classes
        )

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

    @classmethod
    def _get_typing_technical_doc(cls, typing: Typing) -> TypingFullDTO:
        type_: Type[Resource] = typing.get_type()
        if type_ is None:
            return None
        return typing.to_full_dto()

    @classmethod
    def _get_non_typing_obj_technical_doc(cls, obj: Type) -> dict:
        # Get the doc of a class who is not a Resource, Task or Protocol
        doc = {
            "name": obj.__name__,
            "doc": inspect.getdoc(obj)
        }
        members = inspect.getmembers(obj)
        doc["variables"] = []
        doc["methods"] = []
        for name, member  in members:
            if name.startswith("_"):
                continue

            d = inspect.getdoc(member)
            d = d if d is not None else ""

            if callable(member):
                try:
                    signature = inspect.signature(member)
                except TypeError:
                    continue
                except ValueError:
                    continue

                if signature is None:
                    continue
                return_type = signature.return_annotation
                if return_type == inspect._empty:
                    return_type = 'None'
                else:
                    if hasattr(return_type, '__name__'):
                        return_type = return_type.__name__
                    else:
                        return_type = str(return_type)

                args = []
                for arg_name, arg_param in signature.parameters.items():
                    arg_default_value = arg_param.default
                    if arg_default_value == inspect._empty:
                        arg_default_value = 'None'
                    else:
                        if hasattr(arg_default_value, '__name__'):
                            arg_default_value = arg_default_value.__name__
                        else:
                            arg_default_value = str(arg_default_value)

                    arg_type = arg_param.annotation
                    if arg_type == inspect._empty:
                        arg_type = 'None'
                    else:
                        if hasattr(arg_type, '__name__'):
                            arg_type = arg_type.__name__
                        else:
                            arg_type = str(arg_type)
                    args.append({
                        "arg_name": arg_name,
                        "arg_type": arg_type,
                        "arg_default_value": arg_default_value
                    })

                doc["methods"].append({
                    "name": name,
                    "doc": d,
                    "args": args,
                    "return_type": return_type
                })
            else:
                var_type = type(member)
                if var_type.__name__:
                    var_type = var_type.__name__
                else:
                    var_type = str(var_type)
                doc["variables"].append({
                    "name": name,
                    "doc": d,
                    "type": var_type
                })
        return doc
