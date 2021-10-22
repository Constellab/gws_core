
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
            "specs": self.merge_view_method_specs(),
            "default_view": self.default_view,
        }

    def merge_view_method_specs(self) -> ViewConfig:
        json_ = {}

        for key, item in self.specs.items():
            json_[METHOD_SPEC_PREFIX + key] = item.to_json()

        for key, item in self.view_type._specs.items():
            json_[VIEW_SPEC_PREFIX + key] = item.to_json()

        return json_


class ViewConfigValues(BaseModel):

    config_values: Dict[str, Any]

    def get_view_config_values(self) -> Dict[str, Any]:
        return self._get_config_values(VIEW_SPEC_PREFIX)

    def get_method_config_values(self) -> Dict[str, Any]:
        return self._get_config_values(METHOD_SPEC_PREFIX)

    def _get_config_values(self, prefix: str) -> Dict[str, Any]:
        if not self.config_values:
            return {}

        config: Dict[str, Any] = {}

        for key, item in self.config_values.items():
            if key.startswith(prefix):
                config_name = key[len(prefix):]
                config[config_name] = item

        return config
