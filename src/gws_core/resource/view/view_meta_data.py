# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Type

from .view import View
from .view_types import ViewSpecs

METHOD_SPEC_PREFIX: str = 'method_'
VIEW_SPEC_PREFIX: str = 'view_'


class ResourceViewMetaData():
    method_name: str
    view_type: Type[View]
    human_name: str
    short_description: str
    specs: ViewSpecs
    default_view: bool
    hide: bool

    def __init__(self, method_name: str, view_type: Type[View],
                 human_name: str, short_description: str,
                 specs: ViewSpecs, default_view: bool, hide: bool) -> None:
        self.method_name = method_name
        self.view_type = view_type
        self.human_name = human_name
        self.short_description = short_description
        self.specs = specs
        self.default_view = default_view
        self.hide = hide

    def clone(self) -> 'ResourceViewMetaData':
        return ResourceViewMetaData(
            self.method_name, self.view_type, self.human_name, self.short_description, self.specs, self.default_view,
            self.hide)

    def to_json(self) -> dict:
        return {
            "method_name": self.method_name,
            "view_type": self.view_type._type,
            "human_name": self.human_name,
            "short_description": self.short_description,
            "default_view": self.default_view,
        }

    def merge_specs(self) -> ViewSpecs:
        """Merge the view and method specs and return only visible specs"""
        return {**self.view_type._specs, **self.specs}
