
from typing import Any, Dict, Type

from pydantic.main import BaseModel

from ..resource.view import View
from .view_types import ViewSpecs

METHOD_SPEC_PREFIX: str = 'method_'
VIEW_SPEC_PREFIX: str = 'view_'

ViewConfig = Dict[str, Any]


class ResourceViewMetaData():
    method_name: str
    view_type: Type[View]
    human_name: str
    short_description: str
    specs: ViewSpecs
    default_view: bool

    def __init__(self, method_name: str, view_type: Type[View],
                 human_name: str, short_description: str,
                 specs: ViewSpecs, default_view: bool) -> None:
        self.method_name = method_name
        self.view_type = view_type
        self.human_name = human_name
        self.short_description = short_description
        self.specs = specs
        self.default_view = default_view

    def clone(self) -> 'ResourceViewMetaData':
        return ResourceViewMetaData(
            self.method_name, self.view_type, self.human_name, self.short_description, self.specs, self.default_view)

    def to_json(self) -> dict:
        return {
            "method_name": self.method_name,
            "view_type": self.view_type._type,
            "human_name": self.human_name,
            "short_description": self.short_description,
            "specs": self.merge_visible_specs(),
            "default_view": self.default_view,
        }

    def merge_visible_specs(self) -> ViewConfig:
        """Merge the view and method specs and return only visible specs"""
        json_: ViewSpecs = {**self.view_type._specs, **self.specs}

        visible_json = {}
        for key, spec in json_.items():
            if spec.visibility == 'private':
                continue
            visible_json[key] = spec.to_json()
        return visible_json