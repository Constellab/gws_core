# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from multiprocessing.dummy import Process
from typing import List, Type

from gws_core.config.config_specs_helper import ConfigSpecsHelper
from gws_core.core.model.base import Base
from gws_core.io.io_spec_helper import IOSpecs, IOSpecsHelper
from gws_core.model.typing import Typing, TypingObjectType
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.resource import Resource
from gws_core.task.task import Task

from ..resource.resource_typing import ResourceTyping
from .brick_helper import BrickHelper


class TechnicalDocService():

    @classmethod
    def generate_technical_doc(cls, brick_name: str) -> dict:
        """Method to return the technical doc information about a brick to upload it on the hub
        """

        brick_info = BrickHelper.get_brick_info(brick_name)

        return {
            "json_version": 1,
            "brick_name": brick_info["name"],
            "brick_version": brick_info["version"],
            "resources": cls._generate_resource_technical_doc(brick_name),
            "tasks": cls._export_process_technical_doc(brick_name, 'TASK', Task),
        }

    @classmethod
    def _generate_resource_technical_doc(cls, brick_name: str) -> list:

        resource_typings: List[ResourceTyping] = ResourceTyping.get_by_brick(brick_name)
        sorted_resources = sorted(resource_typings, key=lambda x: len(x.get_ancestors()))

        json_list = []
        for resource_typing in sorted_resources:
            json_ = cls._get_typing_technical_doc(resource_typing, Resource)

            if json_ is None:
                continue

            json_list.append(json_)
        return json_list

    @classmethod
    def _export_process_technical_doc(
            cls, brick_name: str, object_type: TypingObjectType, process_type: Type[Process]) -> list:
        process_typings: List[Typing] = Typing.get_by_type_and_brick(object_type, brick_name)
        sorted_processes = sorted(process_typings, key=lambda x: len(x.get_ancestors()))

        json_list = []
        for process_typing in sorted_processes:
            json_ = cls._get_typing_technical_doc(process_typing, process_type)

            if json_ is None:
                continue

            json_["type"] = process_typing.object_sub_type

            type_: Type[Task] = process_typing.get_type()
            json_["input_specs"] = cls._get_io_specs(type_.input_specs)
            json_["output_specs"] = cls._get_io_specs(type_.input_specs)
            json_["config_specs"] = ConfigSpecsHelper.config_specs_to_json(type_.config_specs)

            json_list.append(json_)

        return json_list

    @classmethod
    def _get_io_specs(cls, io_specs: IOSpecs) -> dict:
        json_specs = IOSpecsHelper.io_specs_to_json(io_specs)

        json_list = []
        for name, spec in json_specs.items():

            # retrieve the resource unique names and brick names
            resource_types: List = []
            for resource_type in spec["resource_types"]:
                if resource_type["typing_name"] is None:
                    resource_types.append({"unique_name": None, "brick_name": None})
                else:
                    typing = TypingManager.get_typing_from_name(resource_type["typing_name"])
                    resource_types.append({"unique_name": typing.model_name, "brick_name": typing.brick})

            json_ = {
                "name": name,
                "io_spec": spec["io_spec"],
                "data": spec["data"],
                "resource_types": resource_types
            }

            json_list.append(json_)

        return json_list

    @classmethod
    def _get_typing_technical_doc(cls, typing: Typing, parent_limit_type: Type) -> dict:
        type_: Type[Resource] = typing.get_type()

        if type_ is None:
            return None

        parent: dict = None

        if type_ != parent_limit_type:
            parent_class: Type[Base] = type_.__base__
            # retrieve the typing of the parent class
            parent_typing = Typing.get_by_model_type(parent_class)

            brick_info = BrickHelper.get_brick_info(parent_typing.brick)

            parent = {
                "unique_name": parent_typing.model_name,
                "brick_name": parent_typing.brick,
                "brick_version": brick_info["version"],
                "human_name": parent_typing.human_name
            }

        return{
            "unique_name": typing.model_name,
            "class_name": type_.__name__,
            "human_name": typing.human_name,
            "short_description": typing.short_description,
            "doc": typing.get_model_type_doc(),
            "hide": typing.hide,
            "deprecated_since": typing.deprecated_since,
            "deprecated_message": typing.deprecated_message,
            "parent": parent,
        }
