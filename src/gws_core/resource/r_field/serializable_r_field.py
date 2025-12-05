"""
SerializableRField module for Resource fields with custom serialization logic.

This module provides a framework for creating RFields that store custom Python objects
with manually-defined serialization and deserialization logic to/from JSON-compatible
formats.
"""

from abc import abstractmethod
from typing import Any

from gws_core.core.utils.utils import Utils

from ...core.exception.exceptions.bad_request_exception import BadRequestException
from .r_field import BaseRField


class SerializableObjectJson:
    """Base class for objects that can be serialized to and from JSON.

    SerializableObjectJson defines the interface for custom objects that need to be
    stored in RFields. Objects must implement both serialize and deserialize methods
    to convert between Python objects and JSON-compatible representations.

    This is useful when:
        - You need custom serialization logic not covered by Pydantic
        - You want fine-grained control over the serialization format
        - You're working with complex objects that need special handling
        - You want to maintain backward compatibility with existing formats

    The serialization must produce JSON-compatible types (dict, list, str, bool,
    float, int, None), which can be stored and later deserialized back to the
    original object.

    Example:
        ```python
        class Point(SerializableObjectJson):
            def __init__(self, x: float, y: float):
                self.x = x
                self.y = y

            def serialize(self) -> Dict:
                return {'x': self.x, 'y': self.y}

            @classmethod
            def deserialize(cls, data: Dict) -> 'Point':
                return cls(x=data['x'], y=data['y'])

        class MyResource(Resource):
            location = SerializableRField(object_type=Point)
        ```
    """

    @abstractmethod
    def serialize(self) -> dict | list | str | bool | float:
        """Serialize this object to a JSON-compatible representation.

        This method is called when the Resource containing this object is saved.
        It must return a JSON-compatible type (dict, list, str, bool, float, int, None)
        that can be deserialized back to the object later.

        :return: JSON-compatible representation of this object
        :rtype: Union[Dict, List, str, bool, float]

        Example:
            ```python
            def serialize(self) -> Dict:
                return {
                    'name': self.name,
                    'value': self.value,
                    'metadata': self.metadata
                }
            ```
        """

    @classmethod
    @abstractmethod
    def deserialize(cls, data: dict | list | str | bool | float) -> "SerializableObjectJson":
        """Deserialize a JSON-compatible representation back to an object instance.

        This class method is called when the Resource is loaded from storage.
        It must reconstruct the object from the data produced by the serialize method.

        :param data: JSON-compatible data produced by the serialize method
        :type data: Union[Dict, List, str, bool, float]
        :return: Reconstructed object instance
        :rtype: SerializableObjectJson

        Example:
            ```python
            @classmethod
            def deserialize(cls, data: Dict) -> 'MyObject':
                return cls(
                    name=data['name'],
                    value=data['value'],
                    metadata=data.get('metadata', {})
                )
            ```
        """


class SerializableRField(BaseRField):
    """Resource field for storing custom objects with manual JSON serialization.

    SerializableRField stores instances of SerializableObjectJson subclasses, which
    provide custom serialize() and deserialize() methods for converting between
    Python objects and JSON-compatible representations.

    When a Resource is saved:
        - The object's serialize() method is called
        - The resulting JSON data is stored in KV_STORE

    When a Resource is loaded:
        - The JSON data is retrieved
        - The object's deserialize() class method is called to reconstruct the object

    This is useful for:
        - Custom objects with specific serialization requirements
        - Legacy objects that need special handling
        - Objects that can't use Pydantic (use ModelRField for Pydantic models)
        - Fine-grained control over serialization format

    Storage behavior:
        - Stored in KV_STORE by default
        - Not included in dict views by default (can be changed)
        - Uses custom serialize/deserialize methods

    Example:
        ```python
        class CustomData(SerializableObjectJson):
            def __init__(self, value: int = 0):
                self.value = value

            def serialize(self) -> Dict:
                return {'value': self.value}

            @classmethod
            def deserialize(cls, data: Dict) -> 'CustomData':
                return cls(value=data['value'])

        class MyResource(Resource):
            # Default value is object_type() (new instance)
            data = SerializableRField(object_type=CustomData)

            # Included in dict view
            visible_data = SerializableRField(
                object_type=CustomData,
                include_in_dict_view=True
            )

        # Usage
        resource = MyResource()
        resource.data = CustomData(value=42)
        ```

    Note:
        - The object_type must be a subclass of SerializableObjectJson
        - Default value is a new instance of object_type (calls object_type())
        - The object_type must have a no-argument constructor
    """

    object_type: type[SerializableObjectJson]

    def __init__(
        self, object_type: type[SerializableObjectJson], include_in_dict_view: bool = False
    ) -> None:
        """Initialize a SerializableRField for storing custom serializable objects.

        :param object_type: The SerializableObjectJson subclass that this field will store.
                            Must have a no-argument constructor. A new instance is created
                            as the default value.
        :type object_type: Type[SerializableObjectJson]
        :param include_in_dict_view: If True, this field is included in dict/JSON representations.
                                      Set to False for large or complex objects. Defaults to False
        :type include_in_dict_view: bool, optional
        :raises BadRequestException: If object_type is not a subclass of SerializableObjectJson

        Example:
            ```python
            class MyData(SerializableObjectJson):
                def __init__(self):
                    self.items = []
                # ... implement serialize/deserialize ...

            class MyResource(Resource):
                data = SerializableRField(object_type=MyData)
            ```
        """
        if not Utils.issubclass(object_type, SerializableObjectJson):
            raise BadRequestException(
                "The object type must be a subclass of SerializableObjectJson"
            )
        super().__init__(default_value=object_type, include_in_dict_view=include_in_dict_view)
        self.object_type = object_type

    def deserialize(self, r_field_value: Any) -> SerializableObjectJson:
        """Deserialize JSON data back to a SerializableObjectJson instance.

        This method is called when loading the field from storage. It delegates to
        the object's deserialize() class method to reconstruct the object.

        :param r_field_value: JSON-compatible data produced by serialize(), or None
        :type r_field_value: Any
        :return: Reconstructed object instance, or default value if input is None
        :rtype: SerializableObjectJson
        """
        if r_field_value is None:
            return self.get_default_value()

        return self.object_type.deserialize(r_field_value)

    def serialize(self, r_field_value: SerializableObjectJson) -> Any:
        """Serialize a SerializableObjectJson instance to JSON-compatible data.

        This method is called when saving the field to storage. It delegates to
        the object's serialize() method to convert it to JSON-compatible format.

        :param r_field_value: The SerializableObjectJson instance to serialize, or None
        :type r_field_value: SerializableObjectJson
        :return: JSON-compatible data ready for storage, or None if input is None
        :rtype: Union[Dict, List, str, bool, float, None]
        :raises BadRequestException: If the value is not an instance of the expected object_type
        """
        if r_field_value is None:
            return None

        if not isinstance(r_field_value, self.object_type):
            raise BadRequestException(f"The value must be a {self.object_type.__name__}")

        return r_field_value.serialize()
