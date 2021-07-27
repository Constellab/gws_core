# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..core.exception import BadRequestException
from .resource import Resource


class ResourceSet(Resource):
    """
    ResourceSet class
    """

    _set: dict = None
    _resource_types = (Resource, )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.id is None:
            self.data["set"] = {}
            self._set = {}
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

    def len(self):
        return self.len()

    def __len__(self):
        return len(self.set)

    # -- N --

    def __next__(self):
        return self.set.__next__()

    # -- R --

    def remove(self) -> bool:
        with self.get_db_manager().db.atomic() as transaction:
            for k in self._set:
                if not self._set[k].remove():
                    transaction.rollback()
                    return False
            status = super().remove()
            if not status:
                transaction.rollback()
            return status

    # -- S --

    def __setitem__(self, key, val):
        if not isinstance(val, self._resource_types):
            raise BadRequestException(
                f"The value must be an instance of {self._resource_types}. The actual value is a {type(val)}.")
        self.set[key] = val

    def save(self, *args, **kwrags) -> bool:
        with self.get_db_manager().db.atomic() as transaction:
            self.data["set"] = {}
            for k in self._set:
                if not (self._set[k].is_saved() or self._set[k].save()):
                    transaction.rollback()
                    return False
                self.data["set"][k] = {
                    "uri": self._set[k].uri,
                    "type": self._set[k].full_classname()
                }
            status = super().save(*args, **kwrags)
            if not status:
                transaction.rollback()
            return status

    @property
    def set(self) -> dict:
        from .service.model_service import ModelService
        if self.is_saved() and len(self._set) == 0:
            for k in self.data["set"]:
                uri = self.data["set"][k]["uri"]
                rtype = self.data["set"][k]["type"]
                self._set[k] = ModelService.fetch_model(rtype, uri)
        return self._set

    # -- V --

    def values(self):
        return self.set.values()
