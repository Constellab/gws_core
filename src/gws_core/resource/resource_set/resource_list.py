# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Set

from gws_core.resource.r_field.list_r_field import ListRField

from ..resource import Resource
from ..resource_decorator import resource_decorator
from .resource_list_base import ResourceListBase


@resource_decorator(unique_name="ResourceList", human_name="Resource list",
                    short_description="A list of resources", hide=True)
class ResourceList(ResourceListBase):
    """Resource to manage a list of resources. By default the sytem create a new
    resource for each resource in the set when saving the set

    /!\ for now this resource is only used for DynamicIO. It is not really supposed to be saved in the DB
    """

    # list of resource ids stored
    _resource_ids: List[str] = ListRField()

    # dict provided before the resources are saved
    _resources: List[Resource] = None

    def __init__(self, resources: List[Resource] = None):
        super().__init__()
        self._resources = resources

    def get_resources(self) -> List[Resource]:
        if not self._resources:
            self._resources = list(self._load_resources())

        return self._resources

    def _get_resource_ids(self) -> Set[str]:
        return set(self._resource_ids)

    def get_resources_as_set(self) -> Set[Resource]:
        return set(self.get_resources())

    def _set_r_field(self) -> None:
        """ set _resource_ids with key = resource_name and value = resource_id"""
        self._resource_ids = [resource._model_id for resource in self._resources]

    # add methods to act like a list
    def __getitem__(self, key):
        return self.get_resources()[key]

    def __setitem__(self, key, val):
        self.get_resources()[key] = val

    def __len__(self):
        return len(self.get_resources())

    def __iter__(self):
        return iter(self.get_resources())

    def __contains__(self, item):
        return item in self.get_resources()

    def append(self, item):
        self.get_resources().append(item)

    def extend(self, item):
        self.get_resources().extend(item)

    def insert(self, index, item):
        self.get_resources().insert(index, item)

    def remove(self, item):
        self.get_resources().remove(item)

    def pop(self, index=None):
        return self.get_resources().pop(index)

    def index(self, item):
        return self.get_resources().index(item)

    def count(self, item):
        return self.get_resources().count(item)

    def sort(self, key=None, reverse=False):
        return self.get_resources().sort(key=key, reverse=reverse)

    def reverse(self):
        return self.get_resources().reverse()

    def clear(self):
        return self.get_resources().clear()

    def copy(self):
        return self.get_resources().copy()
