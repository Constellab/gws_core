import inspect
import sys
from typing import Any, List, Type

from gws_core.brick.technical_doc_dto import TechnicalDocDTO
from gws_core.core.utils.reflector_helper import ReflectorHelper
from gws_core.core.utils.reflector_types import (ClassicClassDocDTO,
                                                 MethodDocFunction)
from gws_core.model.typing_dto import TypingFullDTO, TypingStatus
from gws_core.protocol.protocol_typing import ProtocolTyping

from ..model.typing import Typing
from ..resource.resource import Resource
from ..resource.resource_typing import ResourceTyping
from ..task.task_typing import TaskTyping
from .brick_helper import BrickHelper


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
        other_classes = cls.export_other_classes_technical_doc(brick_name, resources + tasks + protocols)

        return TechnicalDocDTO(
            json_version=1,
            brick_name=brick_info.name,
            brick_version=brick_info.version,
            resources=resources,
            tasks=tasks,
            protocols=protocols,
            other_classes=other_classes
        )

    @classmethod
    def export_typing_technical_doc(cls, brick_name: str, typing_class: Type[Typing]) -> List[TypingFullDTO]:
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
    def export_other_classes_technical_doc(
            cls, brick_name: str, resources_tasks_protocols: List[TypingFullDTO]) -> List[ClassicClassDocDTO]:
        other_classes: List[ClassicClassDocDTO] = []
        clsmembers = inspect.getmembers(sys.modules[brick_name], inspect.isclass)

        for name, obj in clsmembers:
            ok = True
            for class_ in resources_tasks_protocols:
                if name == class_.unique_name:
                    ok = False
                    break
            if ok:
                doc: ClassicClassDocDTO = cls._get_non_typing_obj_technical_doc(obj)
                other_classes.append(doc)

        return other_classes

    @classmethod
    def _get_non_typing_obj_technical_doc(cls, obj: Type) -> ClassicClassDocDTO:
        '''
        Get the doc of a class who is not a Resource, Task or Protocol
        '''

        variables = ReflectorHelper.get_all_public_args(obj)

        functions: Any = inspect.getmembers(
            obj, predicate=inspect.isfunction) + inspect.getmembers(obj, predicate=inspect.ismethod)
        public_func_methods: Any = [MethodDocFunction(name=m[0], func=m[1])
                                    for m in functions if not m[0].startswith('_') or m[0] == '__init__']
        methods = ReflectorHelper.get_methods_doc(obj, public_func_methods)

        if not hasattr(obj, '__name__'):
            name = str(obj)
        else:
            name = obj.__name__

        doc = ReflectorHelper.get_cleaned_doc(obj)
        return ClassicClassDocDTO(name=name, doc=doc, methods=methods, variables=variables)

    @classmethod
    def generate_tasks_technical_doc_as_md(cls, brick_name: str, separator: str = None) -> str:
        """Method to return the technical doc information about a brick to upload it on the hub
        """
        tasks = cls.export_typing_technical_doc(brick_name, TaskTyping)

        return cls._generate_objects_technical_doc_as_md(tasks, 'Tasks', separator)

    @classmethod
    def generate_protocols_technical_doc_as_md(cls, brick_name: str, separator: str = None) -> str:
        protocols = cls.export_typing_technical_doc(brick_name, ProtocolTyping)

        return cls._generate_objects_technical_doc_as_md(protocols, 'Protocols', separator)

    @classmethod
    def generate_resources_technical_doc_as_md(cls, brick_name: str, separator: str = None) -> str:
        resources = cls.export_typing_technical_doc(brick_name, ResourceTyping)

        return cls._generate_objects_technical_doc_as_md(resources, 'Resources', separator)

    @classmethod
    def _generate_objects_technical_doc_as_md(cls, objects: List[TypingFullDTO], title: str,
                                              separator: str = None) -> str:
        markdown = f'# {title}\n\n'

        for obj in objects:
            if obj.status == TypingStatus.UNAVAILABLE:
                continue
            if obj.hide:
                continue
            markdown += obj.to_markdown()

            markdown += '\n\n'
            if separator:
                markdown += separator + '\n'

        return markdown
