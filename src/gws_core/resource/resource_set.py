# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from ..core.decorator.transaction import Transaction
from ..core.exception.exceptions import BadRequestException
from ..model.typing_manager import TypingManager
from ..resource.resource import Resource
from ..resource.resource_decorator import ResourceDecorator

@ResourceDecorator("ResourceSet")
class ResourceSet(Resource):
    """
    ResourceSet class
    """

    _set: Dict[str, Resource] = None
    _resource_types = (Resource, )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._set is None:
            self._set = {}

    # -- A --

    def add(self, val):
        if not isinstance(val, self._resource_types):
            raise BadRequestException(
                f"The value must be an instance of {self._resource_types}. The actual value is a {type(val)}.")

        if not val.is_saved():
            val.save()
        self.set[val.uri] = val

    # -- C --

    def __contains__(self, val):
        return val in self.set

    # -- E --

    def exists(self, resource) -> bool:
        return resource in self._set

    # -- G --

    def __getitem__(self, key):
        return self.set[key]

    # -- I --

    def __iter__(self):
        return self.set.__iter__()

    # -- L --

    def len(self) -> int:
        return self.len()

    def __len__(self):
        return len(self.set)

    # -- N --

    def __next__(self):
        return self.set.__next__()

    # -- R --
    @Transaction()
    def remove(self) -> bool:
        for resource in self._set.values():
            resource.remove()
        return super().remove()

    # -- S --

    def __setitem__(self, key, val):
        if not isinstance(val, self._resource_types):
            raise BadRequestException(
                f"The value must be an instance of {self._resource_types}. The actual value is a {type(val)}.")
        self.set[key] = val

    @Transaction()
    def save(self, *args, **kwrags) -> 'ResourceSet':
        self.data["set"] = {}
        for key, resource in self._set.items():
            if not resource.is_saved():
                resource.save()

            self.data["set"][key] = {
                "uri": resource.uri,
                "typing_name": resource.resource_typing_name
            }
        return super().save(*args, **kwrags)

    @property
    def set(self) -> dict:
        if self.is_saved() and len(self._set) == 0:
            for k in self.data["set"]:
                self._set[k] = TypingManager.get_object_with_typing_name_and_uri(
                    self.data["set"][k]["typing_name"], self.data["set"][k]["uri"])
        return self._set

    # -- V --

    def values(self):
        return self.set.values()
