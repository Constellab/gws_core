"""
PrimitiveRField module for Resource fields that store primitive values.

This module provides RFields for storing primitive Python types (int, float, str, bool)
with automatic validation and configurable storage backends. These are the fundamental
building blocks for Resource data fields.
"""

import uuid
from typing import Any

from ...core.classes.validator import (
    BoolValidator,
    FloatValidator,
    IntValidator,
    StrValidator,
    Validator,
)
from .r_field import BaseRField, RFieldStorage


class PrimitiveRField(BaseRField):
    """Base class for Resource fields storing primitive Python types.

    PrimitiveRField provides validation and storage for primitive values (int, float,
    str, bool). This class should not be used directly - use the specific subclasses
    (IntRField, FloatRField, StrRField, BoolRField) instead.

    The field automatically:
        - Validates values using type-specific validators
        - Handles serialization/deserialization
        - Supports configurable storage backends (DATABASE, KV_STORE, NONE)
        - Includes values in dict views by default (configurable)

    Each primitive type has its own validator that ensures type safety during both
    serialization and deserialization operations.

    Attributes:
        validator: Type-specific validator for ensuring data integrity

    Note:
        Use the specific subclasses (IntRField, FloatRField, etc.) rather than
        instantiating this class directly.
    """

    validator: Validator

    def __init__(
        self,
        validator: Validator,
        default_value: Any = None,
        include_in_dict_view: bool = True,
        storage: RFieldStorage = RFieldStorage.KV_STORE,
    ) -> None:
        """Initialize a PrimitiveRField with validation and storage configuration.

        :param validator: Validator used to verify the field value type during serialization
                          and deserialization. Also validates the default value.
        :type validator: Validator
        :param default_value: Default value for the field. Can be:
                              - Primitive value (int, float, str, bool): Used directly
                              - Type or Callable: Called without parameters to generate default
                              - None: Field has no default value
                              Defaults to None
        :type default_value: Any, optional
        :param include_in_dict_view: If True, this field is included in dict/JSON representations.
                                      Primitive fields are included by default. Defaults to True
        :type include_in_dict_view: bool, optional
        :param storage: Storage backend for this field (DATABASE, KV_STORE, or NONE).
                        Defaults to KV_STORE
        :type storage: RFieldStorage, optional
        """
        # check that the default value is correct
        default_value = validator.validate(default_value)
        super().__init__(
            default_value=default_value, include_in_dict_view=include_in_dict_view, storage=storage
        )
        self.validator = validator

    def deserialize(self, r_field_value: Any) -> Any:
        """Deserialize and validate a value from storage.

        Validates the stored value using the field's validator before returning it.

        :param r_field_value: The raw value from storage
        :type r_field_value: Any
        :return: The validated, deserialized value
        :rtype: Any
        """
        validated_value = self.validator.validate(r_field_value)
        return super().deserialize(validated_value)

    def serialize(self, r_field_value: Any) -> Any:
        """Serialize and validate a value for storage.

        Validates the value using the field's validator before storing it.

        :param r_field_value: The runtime value to serialize
        :type r_field_value: Any
        :return: The validated, serialized value
        :rtype: Any
        """
        validated_value = super().serialize(r_field_value)

        return self.validator.validate(validated_value)


class IntRField(PrimitiveRField):
    """Resource field for storing integer values.

    IntRField stores integer values with automatic validation and configurable storage.
    By default, integers are stored in the DATABASE for efficient querying and indexing.

    This is useful for:
        - Counts, indices, and identifiers
        - Numeric metadata (age, quantity, version)
        - Flags represented as integers
        - Small numeric values that need to be searchable

    Storage behavior:
        - Stored in DATABASE by default (searchable and queryable)
        - Included in dict views by default
        - Automatically validated as integer on load/save

    Example:
        ```python
        class MyResource(Resource):
            # Simple counter
            count = IntRField()

            # With default value
            version = IntRField(default_value=1)

            # Stored in KV_STORE instead
            large_id = IntRField(storage=RFieldStorage.KV_STORE)

            # Not included in dict view
            internal_flag = IntRField(include_in_dict_view=False)
        ```
    """

    def __init__(
        self,
        default_value: int | None = None,
        include_in_dict_view: bool = True,
        storage: RFieldStorage = RFieldStorage.DATABASE,
    ) -> None:
        """Initialize an IntRField for storing integer values.

        :param default_value: Default integer value. Can be:
                              - int: A specific integer value
                              - Type or Callable: Called to generate default (e.g., int for 0)
                              - None: Field has no default value
                              Defaults to None
        :type default_value: int | None, optional
        :param include_in_dict_view: If True, included in dict/JSON representations.
                                      Defaults to True for primitive fields
        :type include_in_dict_view: bool, optional
        :param storage: Storage backend (DATABASE for searchable, KV_STORE for simple storage,
                        NONE for transient). Defaults to DATABASE for integers
        :type storage: RFieldStorage, optional
        """
        super().__init__(
            validator=IntValidator(),
            default_value=default_value,
            include_in_dict_view=include_in_dict_view,
            storage=storage,
        )


class FloatRField(PrimitiveRField):
    """Resource field for storing floating-point values.

    FloatRField stores floating-point numeric values with automatic validation and
    configurable storage. By default, floats are stored in the DATABASE for efficient
    querying and indexing.

    This is useful for:
        - Measurements and scientific values
        - Scores, percentages, and ratios
        - Statistical results
        - Any decimal numeric metadata

    Storage behavior:
        - Stored in DATABASE by default (searchable and queryable)
        - Included in dict views by default
        - Automatically validated as float on load/save

    Example:
        ```python
        class MyResource(Resource):
            # Simple measurement
            temperature = FloatRField()

            # With default value
            threshold = FloatRField(default_value=0.95)

            # Stored in KV_STORE instead
            large_value = FloatRField(storage=RFieldStorage.KV_STORE)

            # Not included in dict view
            internal_score = FloatRField(include_in_dict_view=False)
        ```
    """

    def __init__(
        self,
        default_value: float | None = None,
        include_in_dict_view: bool = True,
        storage: RFieldStorage = RFieldStorage.DATABASE,
    ) -> None:
        """Initialize a FloatRField for storing floating-point values.

        :param default_value: Default float value. Can be:
                              - float: A specific floating-point value
                              - Type or Callable: Called to generate default (e.g., float for 0.0)
                              - None: Field has no default value
                              Defaults to None
        :type default_value: float | None, optional
        :param include_in_dict_view: If True, included in dict/JSON representations.
                                      Defaults to True for primitive fields
        :type include_in_dict_view: bool, optional
        :param storage: Storage backend (DATABASE for searchable, KV_STORE for simple storage,
                        NONE for transient). Defaults to DATABASE for floats
        :type storage: RFieldStorage, optional
        """
        super().__init__(
            validator=FloatValidator(),
            default_value=default_value,
            include_in_dict_view=include_in_dict_view,
            storage=storage,
        )


class BoolRField(PrimitiveRField):
    """Resource field for storing boolean values.

    BoolRField stores boolean (True/False) values with automatic validation and
    configurable storage. By default, booleans are stored in the DATABASE for
    efficient querying and filtering.

    This is useful for:
        - Feature flags and toggles
        - Status indicators (is_valid, is_complete, has_error)
        - Binary states and conditions
        - Configuration options

    Storage behavior:
        - Stored in DATABASE by default (searchable and queryable)
        - Included in dict views by default
        - Automatically validated as boolean on load/save

    Example:
        ```python
        class MyResource(Resource):
            # Simple flag
            is_valid = BoolRField()

            # With default value
            is_processed = BoolRField(default_value=False)

            # Stored in KV_STORE instead
            internal_flag = BoolRField(storage=RFieldStorage.KV_STORE)

            # Not included in dict view
            debug_flag = BoolRField(include_in_dict_view=False)
        ```
    """

    def __init__(
        self,
        default_value: bool | None = None,
        include_in_dict_view: bool = True,
        storage: RFieldStorage = RFieldStorage.DATABASE,
    ) -> None:
        """Initialize a BoolRField for storing boolean values.

        :param default_value: Default boolean value. Can be:
                              - bool: True or False
                              - Type or Callable: Called to generate default (e.g., bool for False)
                              - None: Field has no default value
                              Defaults to None
        :type default_value: bool | None, optional
        :param include_in_dict_view: If True, included in dict/JSON representations.
                                      Defaults to True for primitive fields
        :type include_in_dict_view: bool, optional
        :param storage: Storage backend (DATABASE for searchable, KV_STORE for simple storage,
                        NONE for transient). Defaults to DATABASE for booleans
        :type storage: RFieldStorage, optional
        """
        super().__init__(
            validator=BoolValidator(),
            default_value=default_value,
            include_in_dict_view=include_in_dict_view,
            storage=storage,
        )


class StrRField(PrimitiveRField):
    """Resource field for storing string values.

    StrRField stores string values with automatic validation and configurable storage.
    By default, strings are stored in the KV_STORE as they can be large and are not
    typically used for database queries.

    This is useful for:
        - Text content and descriptions
        - Names, labels, and identifiers
        - File paths and URLs
        - Any textual metadata

    Storage behavior:
        - Stored in KV_STORE by default (efficient for larger strings)
        - Included in dict views by default
        - Automatically validated as string on load/save
        - For very large strings, consider setting include_in_dict_view=False

    Example:
        ```python
        class MyResource(Resource):
            # Simple string field
            description = StrRField()

            # With default value
            status = StrRField(default_value='pending')

            # Stored in DATABASE for searchability
            name = StrRField(storage=RFieldStorage.DATABASE)

            # Large content not in dict view
            content = StrRField(include_in_dict_view=False)
        ```
    """

    def __init__(
        self,
        default_value: str | None = None,
        include_in_dict_view: bool = True,
        storage: RFieldStorage = RFieldStorage.KV_STORE,
    ) -> None:
        """Initialize a StrRField for storing string values.

        :param default_value: Default string value. Can be:
                              - str: A specific string value
                              - Type or Callable: Called to generate default (e.g., str for '')
                              - None: Field has no default value
                              Defaults to None
        :type default_value: str | None, optional
        :param include_in_dict_view: If True, included in dict/JSON representations.
                                      Set to False for very large strings. Defaults to True
        :type include_in_dict_view: bool, optional
        :param storage: Storage backend (DATABASE for searchable but limited size,
                        KV_STORE for larger strings, NONE for transient).
                        Defaults to KV_STORE for strings
        :type storage: RFieldStorage, optional
        """
        super().__init__(
            validator=StrValidator(),
            default_value=default_value,
            include_in_dict_view=include_in_dict_view,
            storage=storage,
        )


class UUIDRField(StrRField):
    """Resource field for storing UUID (Universally Unique Identifier) values.

    UUIDRField is a specialized StrRField that automatically generates a unique UUID
    as the default value. Each Resource instance gets its own unique identifier.

    This is useful for:
        - Unique identifiers for resources
        - Tracking and correlation IDs
        - External system references
        - Ensuring uniqueness across distributed systems

    Storage behavior:
        - Stored in KV_STORE by default (inherited from StrRField)
        - Included in dict views by default
        - Automatically generates a new UUID if no value is set
        - UUID format: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

    Example:
        ```python
        class MyResource(Resource):
            # Automatically gets a unique UUID
            tracking_id = UUIDRField()

            # Stored in DATABASE for searchability
            external_id = UUIDRField(storage=RFieldStorage.DATABASE)

            # Not included in dict view
            internal_uuid = UUIDRField(include_in_dict_view=False)

        # Usage
        resource = MyResource()
        print(resource.tracking_id)  # e.g., "550e8400-e29b-41d4-a716-446655440000"
        ```

    Note:
        - A new UUID is generated for each Resource instance
        - UUIDs are version 4 (random) by default
        - Cannot specify a default_value (always uses uuid.uuid4())
    """

    def __init__(
        self, include_in_dict_view: bool = True, storage: RFieldStorage = RFieldStorage.KV_STORE
    ) -> None:
        """Initialize a UUIDRField that automatically generates unique identifiers.

        Note: Unlike other fields, UUIDRField does not accept a default_value parameter
        as it always generates a new UUID for each instance.

        :param include_in_dict_view: If True, included in dict/JSON representations.
                                      Defaults to True
        :type include_in_dict_view: bool, optional
        :param storage: Storage backend (DATABASE for searchable, KV_STORE for simple storage,
                        NONE for transient). Defaults to KV_STORE
        :type storage: RFieldStorage, optional
        """
        super().__init__(include_in_dict_view=include_in_dict_view, storage=storage)

    def get_default_value(self) -> Any:
        """Generate a new UUID v4 as the default value.

        This method is called each time a new Resource instance is created, ensuring
        that each instance gets a unique identifier.

        :return: String representation of a new UUID v4
        :rtype: str
        """
        return str(uuid.uuid4())
