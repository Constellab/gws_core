"""
RField module for defining resource fields with different storage backends.

This module provides the core infrastructure for defining fields on Resource objects
that can be automatically persisted and retrieved from different storage backends.
"""

from enum import Enum
from inspect import isclass, isfunction
from typing import Any, Callable, Type, Union

from ...core.exception.exceptions.bad_request_exception import BadRequestException


class RFieldStorage(Enum):
    """Enum defining storage backend options for RField values.

    RFieldStorage determines where and how a field's value is persisted when a Resource
    is saved, and how it is retrieved when the Resource is loaded.

    Attributes:
        DATABASE: Store field value in the relational database.
            - Pros: Searchable, queryable, indexed for fast lookups
            - Cons: Limited to small data sizes, slower for large values
            - Use for: Metadata, identifiers, small structured data
            - Example: count=5, name="result", is_valid=True

        KV_STORE: Store field value in a key-value store.
            - Pros: Handles larger data, efficient storage and retrieval
            - Cons: Not directly searchable, lazy-loaded when accessed
            - Use for: Large strings, serialized data, binary blobs
            - Example: Large text content, JSON data, file contents

        NONE: Do not persist the field value.
            - Only use when you know what you are doing
            - Note: Values can be provided via ResourceFactory.create_resource(additional_data=...)

    Example:
        ```python
        class MyResource(Resource):
            # Small searchable metadata - stored in database
            item_count = IntRField(storage=RFieldStorage.DATABASE)

            # Large content - stored in KV store
            description = StrRField(storage=RFieldStorage.KV_STORE)

            # Temporary computed value - not persisted
            is_processed = BoolRField(storage=RFieldStorage.NONE)
        ```
    """

    DATABASE = "database"
    KV_STORE = "kv_store"
    NONE = "none"


class BaseRField:
    """Base class for all Resource fields with automatic persistence.

    BaseRField provides the foundation for defining fields on Resource objects that are
    automatically persisted and restored based on their storage configuration.

    When a Resource is output from a task:
        - Fields are serialized and saved to their configured storage backend
        - DATABASE fields are stored in the relational database
        - KV_STORE fields are stored in the key-value store
        - NONE fields are not persisted

    When a Resource is loaded as task input:
        - Fields are deserialized from their storage backend
        - DATABASE fields are loaded from the database
        - KV_STORE fields are lazy-loaded when accessed
        - NONE fields use default values (or can be provided via additional_data)

    Attributes:
        storage: The storage backend for this field (DATABASE, KV_STORE, or NONE)
        include_in_dict_view: Whether this field is included in dict representations
        _default_value: The default value or factory function for this field
    """

    storage: RFieldStorage
    include_in_dict_view: bool
    _default_value: Any

    def __init__(
        self,
        default_value: Union[Type, Callable[[], Any], int, float, str, bool] = None,
        include_in_dict_view: bool = False,
        storage: RFieldStorage = RFieldStorage.KV_STORE,
    ) -> None:
        """Initialize a BaseRField with storage and default value configuration.

        :param default_value: Default value for the field when not set. Can be:
                              - Primitive value (int, float, str, bool): Used directly
                              - Type or Callable: Called without parameters to generate the default
                              - None: Field has no default value
                              Defaults to None
        :type default_value: Union[Type, Callable[[], Any], int, float, str, bool], optional
        :param include_in_dict_view: If True, this field is included in dict/JSON representations.
                                      Set to False for large or sensitive data. Defaults to False
        :type include_in_dict_view: bool, optional
        :param storage: Storage backend for this field. Determines persistence behavior.
                        Defaults to KV_STORE for efficient storage of larger values
        :type storage: RFieldStorage, optional

        Example:
            ```python
            # Primitive default value
            field1 = BaseRField(default_value=0, storage=RFieldStorage.DATABASE)

            # Callable default value (called each time)
            field2 = BaseRField(default_value=list, storage=RFieldStorage.KV_STORE)

            # No default, transient field
            field3 = BaseRField(storage=RFieldStorage.NONE)
            ```
        """
        self.storage = storage
        self._default_value = default_value
        self.include_in_dict_view = include_in_dict_view

    @property
    def searchable(self) -> bool:
        """Legacy property for backward compatibility.

        Returns True if the field is stored in the DATABASE (making it searchable).
        This property exists for backward compatibility with code that used the
        previous 'searchable' boolean parameter.

        :return: True if storage is DATABASE, False otherwise
        :rtype: bool
        """
        return self.storage == RFieldStorage.DATABASE

    def deserialize(self, r_field_value: Any) -> Any:
        """Convert a stored value into the field's runtime representation.

        Called when loading a field value from storage. Override this method in
        subclasses to implement custom deserialization logic.

        :param r_field_value: The raw value retrieved from storage
        :type r_field_value: Any
        :return: The deserialized value ready for use in the Resource
        :rtype: Any
        """
        if r_field_value is None:
            return self.get_default_value()

        return r_field_value

    def serialize(self, r_field_value: Any) -> Any:
        """Convert the field's runtime value into a storable representation.

        Called when saving a field value to storage. Override this method in
        subclasses to implement custom serialization logic.

        :param r_field_value: The current field value in the Resource
        :type r_field_value: Any
        :return: The serialized value ready for storage
        :rtype: Any
        """
        if r_field_value is None:
            return self.get_default_value()

        return r_field_value

    def get_default_value(self) -> Any:
        """Get the default value for this field.

        If the default value is a Type or Callable, it will be called to generate
        a new default value. Otherwise, the default value is returned directly.

        This ensures that mutable defaults (like lists or dicts) are not shared
        between Resource instances.

        :return: The default value for this field
        :rtype: Any
        :raises BadRequestException: If the default value is not a primitive, Type, or Callable
        """
        if self._default_value is None:
            return None

        # If the default value is a type or function, call it to generate a new instance
        # This prevents sharing mutable objects between Resource instances
        if isclass(self._default_value) or isfunction(self._default_value):
            return self._default_value()

        # Only allow primitive types as direct default values
        # Using mutable objects (list, dict, etc.) would be dangerous as all
        # Resource instances would share the same object
        if not isinstance(self._default_value, (int, bool, str, float)):
            raise BadRequestException(
                f"Invalid default value '{str(self._default_value)}' for the RField. "
                f"Only primitive values (int, float, bool, str), types, or functions are supported."
            )

        return self._default_value


class RField(BaseRField):
    """Resource field with custom serialization/deserialization support.

    RField extends BaseRField to provide custom serialization and deserialization logic.
    This is useful when the field value needs special handling for storage (e.g., complex
    objects, encrypted data, compressed content).

    The field is automatically persisted when a Resource is output from a task and
    automatically restored when the Resource is loaded as input to another task.

    Custom serialization can be implemented in two ways:
    1. Pass serializer/deserializer functions to __init__
    2. Subclass RField and override the serialize/deserialize methods

    Attributes:
        _deserializer: Optional function to convert stored values to runtime values
        _serializer: Optional function to convert runtime values to storable values

    Example:
        ```python
        import json

        class MyResource(Resource):
            # Using serializer/deserializer functions
            metadata = RField(
                serializer=lambda x: json.dumps(x),
                deserializer=lambda x: json.loads(x),
                default_value=dict,
                storage=RFieldStorage.KV_STORE
            )

            # Simple field with no custom serialization
            description = RField(storage=RFieldStorage.KV_STORE)
        ```

        ```python
        # Alternative: Subclass approach
        class JsonRField(RField):
            def serialize(self, value):
                return json.dumps(value) if value is not None else None

            def deserialize(self, value):
                return json.loads(value) if value is not None else None
        ```
    """

    _deserializer: Callable[[Any], Any] | None
    _serializer: Callable[[Any], Any] | None

    def __init__(
        self,
        deserializer: Callable[[Any], Any] | None = None,
        serializer: Callable[[Any], Any] | None = None,
        default_value: Union[type, Callable[[], Any], int, float, str, bool, None] = None,
        include_in_dict_view: bool = False,
        storage: RFieldStorage = RFieldStorage.KV_STORE,
    ) -> None:
        """Initialize an RField with optional custom serialization logic.

        :param deserializer: Function to deserialize stored values (storage -> runtime).
                             Signature: (stored_value: Any) -> runtime_value: Any
                             If None, no custom deserialization is performed. Defaults to None
        :type deserializer: Callable[[Any], Any] | None, optional
        :param serializer: Function to serialize runtime values (runtime -> storage).
                           Signature: (runtime_value: Any) -> stored_value: Any
                           If None, no custom serialization is performed. Defaults to None
        :type serializer: Callable[[Any], Any] | None, optional
        :param default_value: Default value for the field. Can be a primitive, Type, or Callable.
                              See BaseRField.__init__ for details. Defaults to None
        :type default_value: Union[type, Callable[[], Any], int, float, str, bool, None], optional
        :param include_in_dict_view: Whether to include this field in dict/JSON views.
                                      Use False for large or sensitive data. Defaults to False
        :type include_in_dict_view: bool, optional
        :param storage: Storage backend for persistence (DATABASE, KV_STORE, or NONE).
                        Defaults to KV_STORE for efficient storage of larger values
        :type storage: RFieldStorage, optional
        """
        super().__init__(
            default_value=default_value, include_in_dict_view=include_in_dict_view, storage=storage
        )
        self._deserializer = deserializer
        self._serializer = serializer

    def deserialize(self, r_field_value: Any) -> Any:
        """Deserialize a stored value into the field's runtime representation.

        This method is called when loading a field value from storage. If a custom
        deserializer function was provided during initialization, it will be used.
        Otherwise, the value is returned as-is.

        Can be overridden in subclasses to implement class-level deserialization logic.

        :param r_field_value: The raw value retrieved from storage
        :type r_field_value: Any
        :return: The deserialized runtime value
        :rtype: Any

        Example:
            ```python
            # With deserializer function
            field = RField(deserializer=json.loads)
            value = field.deserialize('{"key": "value"}')  # Returns dict

            # Subclass override
            class DateRField(RField):
                def deserialize(self, value):
                    return datetime.fromisoformat(value) if value else None
            ```
        """
        if r_field_value is None:
            return self.get_default_value()

        if self._deserializer is None:
            return r_field_value

        return self._deserializer(r_field_value)

    def serialize(self, r_field_value: Any) -> Any:
        """Serialize the field's runtime value into a storable representation.

        This method is called when saving a field value to storage. If a custom
        serializer function was provided during initialization, it will be used.
        Otherwise, the value is returned as-is.

        Can be overridden in subclasses to implement class-level serialization logic.

        :param r_field_value: The current runtime value in the Resource
        :type r_field_value: Any
        :return: The serialized value ready for storage
        :rtype: Any

        Example:
            ```python
            # With serializer function
            field = RField(serializer=json.dumps)
            value = field.serialize({"key": "value"})  # Returns string

            # Subclass override
            class DateRField(RField):
                def serialize(self, value):
                    return value.isoformat() if value else None
            ```
        """
        if r_field_value is None:
            return self.get_default_value()

        if self._serializer is None:
            return r_field_value

        return self._serializer(r_field_value)
