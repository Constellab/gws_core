# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from abc import abstractmethod
from typing import Any, Dict, List, Type, Union

from gws_core.core.utils.utils import Utils

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .r_field import BaseRField


class SerializableObject():
    """Serializable and deserializable object. It must be serialized into a json object and deserialized from a json object."""

    def __init__(self):
        pass

    @abstractmethod
    def serialize(self) -> Union[Dict, List, str, bool, float]:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: Union[Dict, List, str, bool, float]) -> 'SerializableObject':
        pass


class SerializableRField(BaseRField):

    object_type: Type[SerializableObject]

    def __init__(self, object_type: Type[SerializableObject], include_in_dict_view: bool = False) -> None:
        """
        RField to serialize and deserialize python object to and from json
        :param object_type: type of the jsonable object. This type is instantiated when the resource is created. It must have a constructor with no parameter.
        :type object_type: Type[SerializableObject], optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to False
        :type include_in_dict_view: bool, optional
        """
        if not Utils.issubclass(object_type, SerializableObject):
            raise BadRequestException("The object type must be a subclass of SerializableObject")
        super().__init__(searchable=False,
                         default_value=object_type, include_in_dict_view=include_in_dict_view)
        self.object_type = object_type

    def deserialize(self, r_field_value: Any) -> SerializableObject:
        if r_field_value is None:
            return self.get_default_value()

        return self.object_type.deserialize(r_field_value)

    def serialize(self, r_field_value: SerializableObject) -> Any:
        if r_field_value is None:
            return None

        if not isinstance(r_field_value, self.object_type):
            raise BadRequestException(f"The value must be a {self.object_type.__name__}")

        return r_field_value.serialize()
