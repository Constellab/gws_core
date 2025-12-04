"""
ListRField module for Resource fields that store JSON-like lists.

This module provides an RField for storing lists with JSON-compatible values.
The field automatically handles serialization and ensures data integrity through
validation and JSON conversion.
"""

from typing import Any, List

from gws_core.core.utils.json_helper import JSONHelper

from ...core.classes.validator import ListValidator
from ...core.exception.exceptions.bad_request_exception import BadRequestException
from .primitive_r_field import PrimitiveRField


class ListRField(PrimitiveRField):
    """Resource field for storing JSON-like lists.

    ListRField stores list data with automatic JSON serialization and validation.
    It only supports JSON-compatible values: primitives (str, int, float, bool, None),
    nested dictionaries, and nested lists of these types.

    The field automatically:
        - Converts Python objects to JSON-compatible format using str()
        - Replaces NaN and Inf values with None
        - Validates that values are lists
        - Provides an empty list [] as default if no default_value is specified

    This is useful for:
        - Storing collections of items
        - Arrays of primitives or objects
        - Ordered data sequences
        - API responses with list data

    Storage behavior:
        - Stored in KV_STORE by default (inherited from PrimitiveRField)
        - Not included in dict views by default (can be changed)
        - Automatically serialized to JSON on save
        - Automatically deserialized from JSON on load

    Example:
        ```python
        class MyResource(Resource):
            # Simple list of items
            items = ListRField()

            # With default value
            tags = ListRField(default_value=['default', 'tags'])

            # Included in dict view
            categories = ListRField(include_in_dict_view=True)

        # Usage
        resource = MyResource()
        resource.items = [1, 2, 3, 'text']
        resource.tags.append('new_tag')
        resource.categories = [{'name': 'cat1', 'id': 1}, {'name': 'cat2', 'id': 2}]
        ```

    Note:
        - Non-JSON-compatible objects are converted to strings
        - NaN and Inf are replaced with None for JSON compatibility
        - Nested structures must also be JSON-compatible
        - Lists can contain mixed types as long as they're JSON-compatible
    """

    def __init__(
        self, default_value: List | None = None, include_in_dict_view: bool = False
    ) -> None:
        """Initialize a ListRField for storing JSON-like lists.

        :param default_value: Default value for the field when not set. Can be:
                              - List: A list with JSON-compatible values
                              - Type or Callable: Called without parameters to generate default (e.g., list)
                              - None: Defaults to empty list []
                              The default value must be JSON-serializable. Defaults to None (uses [])
        :type default_value: List | None, optional
        :param include_in_dict_view: If True, this field is included in dict/JSON representations.
                                      Set to False for large lists to avoid performance issues.
                                      Defaults to False
        :type include_in_dict_view: bool, optional
        :raises BadRequestException: If default_value is not a valid JSON-like list

        Example:
            ```python
            # Empty list default
            field1 = ListRField()

            # Static default value
            field2 = ListRField(default_value=[1, 2, 3])

            # Callable default (creates new list each time)
            field3 = ListRField(default_value=list)

            # Included in dict view
            field4 = ListRField(include_in_dict_view=True)
            ```
        """
        super().__init__(
            validator=ListValidator(),
            default_value=default_value,
            include_in_dict_view=include_in_dict_view,
        )

    def get_default_value(self) -> Any:
        """Get the default value for this field.

        Returns an empty list if no default value was specified. If a default
        value was provided, it is converted to JSON format to ensure compatibility.

        :return: The default list value
        :rtype: List
        :raises BadRequestException: If the default value cannot be converted to JSON format
        """
        if self._default_value is None:
            return []

        try:
            return JSONHelper.convert_dict_to_json(self._default_value)
        except:
            raise BadRequestException(
                "Incorrect default value for ListRField. The default value must be a json like list"
            )

    def serialize(self, r_field_value: Any) -> Any:
        """Serialize the list value for storage.

        Converts the list to JSON-compatible format by:
            - Converting non-JSON objects to strings
            - Replacing NaN and Inf with None
            - Ensuring nested structures are JSON-compatible

        :param r_field_value: The list value to serialize
        :type r_field_value: Any
        :return: JSON-compatible list ready for storage
        :rtype: List
        """
        return super().serialize(JSONHelper.convert_dict_to_json(r_field_value))
