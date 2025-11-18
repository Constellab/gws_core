

"""
ModelRField module for Resource fields that store Pydantic models.

This module provides an RField for storing BaseModelDTO objects with automatic
JSON serialization and deserialization using Pydantic. This ensures type safety,
validation, and clean serialization for structured data objects.
"""

from typing import Any, Type

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.utils import Utils

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .r_field import BaseRField


class ModelRfield(BaseRField):
    """Resource field for storing Pydantic BaseModelDTO objects.

    ModelRfield provides automatic serialization and deserialization of Pydantic models
    (BaseModelDTO) to and from JSON. This ensures type-safe, validated storage of
    structured data objects with all the benefits of Pydantic.

    The field automatically:
        - Serializes model instances to JSON strings using Pydantic
        - Deserializes JSON strings back to model instances
        - Validates data according to Pydantic model schema
        - Provides type hints and IDE support
        - Handles nested models and complex types

    This is useful for:
        - Storing structured configuration objects
        - Complex data models with validation
        - API response objects
        - Typed data structures
        - Objects with nested relationships

    Storage behavior:
        - Stored in KV_STORE by default
        - Not included in dict views by default (can be changed)
        - Automatically serialized to JSON on save
        - Automatically deserialized and validated on load

    Example:
        ```python
        from gws_core.core.model.model_dto import BaseModelDTO
        from pydantic import Field

        class UserConfig(BaseModelDTO):
            name: str
            age: int = Field(ge=0)
            email: str

        class MyResource(Resource):
            # Store a user configuration object
            user_config = ModelRfield(object_type=UserConfig)

            # Included in dict view
            summary = ModelRfield(object_type=SummaryDTO, include_in_dict_view=True)

        # Usage
        resource = MyResource()
        resource.user_config = UserConfig(name='John', age=30, email='john@example.com')
        # Validation happens automatically via Pydantic
        ```

    Note:
        - The object_type must be a subclass of BaseModelDTO
        - Pydantic validation is applied during deserialization
        - Models can have complex nested structures
        - Default value is None (model is not instantiated by default)
    """
    object_type: Type[BaseModelDTO]

    def __init__(self, object_type: Type[BaseModelDTO], include_in_dict_view: bool = False) -> None:
        """Initialize a ModelRfield for storing Pydantic model objects.

        :param object_type: The Pydantic model class (subclass of BaseModelDTO) that this field will store.
                            Must be a valid Pydantic model with proper validation schema.
        :type object_type: Type[BaseModelDTO]
        :param include_in_dict_view: If True, this field is included in dict/JSON representations.
                                      Set to False for large or complex models. Defaults to False
        :type include_in_dict_view: bool, optional
        :raises BadRequestException: If object_type is not a subclass of BaseModelDTO

        Example:
            ```python
            class MyDTO(BaseModelDTO):
                field1: str
                field2: int

            class MyResource(Resource):
                data = ModelRfield(object_type=MyDTO)
                visible_data = ModelRfield(object_type=MyDTO, include_in_dict_view=True)
            ```
        """
        if not Utils.issubclass(object_type, BaseModelDTO):
            raise BadRequestException("The object type must be a subclass of BaseModelDTO")
        super().__init__(default_value=None, include_in_dict_view=include_in_dict_view)  # type: ignore
        self.object_type = object_type

    def deserialize(self, r_field_value: Any) -> BaseModelDTO:
        """Deserialize a JSON string into a Pydantic model instance.

        This method is called when loading the field from storage. It uses Pydantic's
        from_json_str method to deserialize and validate the data.

        :param r_field_value: JSON string representation of the model, or None
        :type r_field_value: Any
        :return: Deserialized and validated model instance, or None if input is None
        :rtype: BaseModelDTO
        :raises ValidationError: If the JSON data doesn't match the model schema
        """
        if r_field_value is None:
            return self.get_default_value()

        return self.object_type.from_json_str(r_field_value)

    def serialize(self, r_field_value: BaseModelDTO) -> Any:
        """Serialize a Pydantic model instance to a JSON string.

        This method is called when saving the field to storage. It uses Pydantic's
        to_json_str method to serialize the model.

        :param r_field_value: The Pydantic model instance to serialize, or None
        :type r_field_value: BaseModelDTO
        :return: JSON string representation of the model, or None if input is None
        :rtype: str | None
        :raises BadRequestException: If the value is not an instance of the expected model type
        """
        if r_field_value is None:
            return None

        if not isinstance(r_field_value, self.object_type):
            raise BadRequestException(f"The value must be a {self.object_type.__name__}")

        return r_field_value.to_json_str()
