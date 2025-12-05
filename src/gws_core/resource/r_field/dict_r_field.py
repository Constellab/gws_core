"""
DictRField module for Resource fields that store JSON-like dictionaries.

This module provides an RField for storing dictionaries with JSON-compatible values.
The field automatically handles serialization and ensures data integrity through
validation and JSON conversion.
"""

from typing import Any

from gws_core.core.classes.validator import DictValidator
from gws_core.core.utils.json_helper import JSONHelper

from ...core.exception.exceptions.bad_request_exception import BadRequestException
from .primitive_r_field import PrimitiveRField


class DictRField(PrimitiveRField):
    """Resource field for storing JSON-like dictionaries.

    DictRField stores dictionary data with automatic JSON serialization and validation.
    It only supports JSON-compatible values: primitives (str, int, float, bool, None),
    nested dictionaries, and lists of these types.

    The field automatically:
        - Converts Python objects to JSON-compatible format using str()
        - Replaces NaN and Inf values with None
        - Validates that values are dictionaries
        - Provides an empty dict {} as default if no default_value is specified

    This is useful for:
        - Storing metadata and configuration
        - Nested structured data
        - API responses and JSON data
        - Key-value mappings

    Storage behavior:
        - Stored in KV_STORE by default (inherited from PrimitiveRField)
        - Not included in dict views by default (can be changed)
        - Automatically serialized to JSON on save
        - Automatically deserialized from JSON on load

    Example:
        ```python
        class MyResource(Resource):
            # Simple metadata dictionary
            metadata = DictRField()

            # With default value
            config = DictRField(default_value={'key': 'value'})

            # Included in dict view
            summary = DictRField(include_in_dict_view=True)

        # Usage
        resource = MyResource()
        resource.metadata = {'author': 'John', 'version': 1}
        resource.config['new_key'] = 'new_value'
        ```

    Note:
        - Non-JSON-compatible objects are converted to strings
        - NaN and Inf are replaced with None for JSON compatibility
        - Nested structures must also be JSON-compatible
    """

    def __init__(
        self, default_value: dict | None = None, include_in_dict_view: bool = False
    ) -> None:
        """Initialize a DictRField for storing JSON-like dictionaries.

        :param default_value: Default value for the field when not set. Can be:
                              - Dict: A dictionary with JSON-compatible values
                              - Type or Callable: Called without parameters to generate default (e.g., dict)
                              - None: Defaults to empty dict {}
                              The default value must be JSON-serializable. Defaults to None (uses {})
        :type default_value: Dict | None, optional
        :param include_in_dict_view: If True, this field is included in dict/JSON representations.
                                      Set to False for large dictionaries to avoid performance issues.
                                      Defaults to False
        :type include_in_dict_view: bool, optional
        :raises BadRequestException: If default_value is not a valid JSON-like dictionary

        Example:
            ```python
            # Empty dict default
            field1 = DictRField()

            # Static default value
            field2 = DictRField(default_value={'status': 'pending'})

            # Callable default (creates new dict each time)
            field3 = DictRField(default_value=dict)

            # Included in dict view
            field4 = DictRField(include_in_dict_view=True)
            ```
        """
        super().__init__(
            validator=DictValidator(),
            default_value=default_value,
            include_in_dict_view=include_in_dict_view,
        )

    def get_default_value(self) -> Any:
        """Get the default value for this field.

        Returns an empty dictionary if no default value was specified. If a default
        value was provided, it is converted to JSON format to ensure compatibility.

        :return: The default dictionary value
        :rtype: Dict
        :raises BadRequestException: If the default value cannot be converted to JSON format
        """
        if self._default_value is None:
            return {}
        try:
            return JSONHelper.convert_dict_to_json(self._default_value)
        except:
            raise BadRequestException(
                "Incorrect default value for DictRField. The default value must be a json like dictionary"
            )

    def serialize(self, r_field_value: Any) -> Any:
        """Serialize the dictionary value for storage.

        Converts the dictionary to JSON-compatible format by:
            - Converting non-JSON objects to strings
            - Replacing NaN and Inf with None
            - Ensuring nested structures are JSON-compatible

        :param r_field_value: The dictionary value to serialize
        :type r_field_value: Any
        :return: JSON-compatible dictionary ready for storage
        :rtype: Dict
        """
        return super().serialize(JSONHelper.convert_dict_to_json(r_field_value))
