

from typing import Any, Type

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.utils import Utils

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .r_field import BaseRField


class ModelRfield(BaseRField):
    """
    RField to serialize and deserialize BaseModelDTO to and from json using pydantic.
    """
    object_type: Type[BaseModelDTO]

    def __init__(self, object_type: Type[BaseModelDTO], include_in_dict_view: bool = False) -> None:
        """
        RField to serialize and deserialize BaseModelDTO to and from json using pydantic.
        :param object_type: type of the jsonable object. This type is instantiated when the resource is created. It must have a constructor with no parameter.
        :type object_type: Type[SerializableObject], optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to False
        :type include_in_dict_view: bool, optional
        """
        if not Utils.issubclass(object_type, BaseModelDTO):
            raise BadRequestException("The object type must be a subclass of SerializableObject")
        super().__init__(searchable=False,
                         default_value=None, include_in_dict_view=include_in_dict_view)
        self.object_type = object_type

    def deserialize(self, r_field_value: Any) -> BaseModelDTO:
        if r_field_value is None:
            return self.get_default_value()

        return self.object_type.from_json_str(r_field_value)

    def serialize(self, r_field_value: BaseModelDTO) -> Any:
        if r_field_value is None:
            return None

        if not isinstance(r_field_value, self.object_type):
            raise BadRequestException(f"The value must be a {self.object_type.__name__}")

        return r_field_value.to_json_str()
