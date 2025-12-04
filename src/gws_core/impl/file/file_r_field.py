"""
FileRField module for Resource fields that persist data to files.

This module provides an abstract base class for creating RFields that store their
data in files rather than directly in the database or key-value store. The file
path is stored, and the actual data is loaded/saved via custom implementations.
"""

from abc import abstractmethod
from typing import Any, final

from ...resource.r_field.r_field import BaseRField, RFieldStorage


class FileRField(BaseRField):
    """Abstract base class for Resource fields that persist data to files.

    FileRField provides a framework for RFields that store their data in files on disk.
    The field stores a file path reference, and subclasses implement custom logic for
    reading from and writing to these files.

    When a Resource is saved:
        - The `dump_to_file` method is called with the field value and file path
        - The file path is stored in the KV_STORE for later retrieval

    When a Resource is loaded:
        - The file path is retrieved from storage
        - The `load_from_file` method is called to read and deserialize the data

    This is useful for:
        - Large data that shouldn't be stored in database/KV_STORE directly
        - Binary data (images, audio, video, archives)
        - Data formats that benefit from file-based storage (HDF5, Parquet, etc.)
        - Custom serialization formats

    Note:
        - Fields are never included in dict views (include_in_dict_view=False)
        - Storage is always KV_STORE (stores file path reference)
        - Subclasses must implement both load_from_file and dump_to_file methods

    Example:
        ```python
        import pickle

        class PickleRField(FileRField):
            '''RField that stores data as pickle files'''

            def load_from_file(self, file_path: str) -> Any:
                with open(file_path, 'rb') as f:
                    return pickle.load(f)

            def dump_to_file(self, r_field_value: Any, file_path: str) -> None:
                with open(file_path, 'wb') as f:
                    pickle.dump(r_field_value, f)

        class MyResource(Resource):
            large_data = PickleRField()
        ```
    """

    def __init__(self, default_value: Any = None) -> None:
        """Initialize a FileRField with automatic file-based persistence.

        The field is configured to store file path references in KV_STORE and is
        excluded from dict views since the actual data is in files.

        :param default_value: Default value for the field when not set. Can be:
                              - Primitive value: Used directly as default
                              - Type or Callable: Called without parameters to generate default
                              - None: Field has no default value
                              Defaults to None
        :type default_value: Any, optional
        """
        super().__init__(
            default_value=default_value, include_in_dict_view=False, storage=RFieldStorage.KV_STORE
        )

    @final
    def deserialize(self, r_field_value: str) -> Any:
        """Deserialize field value by loading data from the file path.

        This method is marked as final and cannot be overridden. It delegates to
        the `load_from_file` method which must be implemented by subclasses.

        :param r_field_value: File path where the data is stored
        :type r_field_value: str
        :return: The deserialized object loaded from the file
        :rtype: Any
        """
        return self.load_from_file(r_field_value)

    @final
    def serialize(self, r_field_value: Any) -> str:
        """Serialize method not used for FileRField.

        The actual serialization is handled by `dump_to_file` which is called
        by the resource persistence layer. This method exists for interface
        compatibility but should be ignored.

        :param r_field_value: The field value (ignored)
        :type r_field_value: Any
        :return: Empty string placeholder
        :rtype: str
        """
        return ""

    @abstractmethod
    def load_from_file(self, file_path: str) -> Any:
        """Load and deserialize the field value from a file.

        This abstract method must be implemented by subclasses to define how data
        is read and deserialized from the file. It is called automatically when
        the Resource is loaded.

        The file at `file_path` is guaranteed to exist when this method is called.

        :param file_path: Absolute path to the file containing the serialized data
        :type file_path: str
        :return: The deserialized object loaded from the file
        :rtype: Any

        Example:
            ```python
            def load_from_file(self, file_path: str) -> pd.DataFrame:
                return pd.read_csv(file_path)
            ```
        """

    @abstractmethod
    def dump_to_file(self, r_field_value: Any, file_path: str) -> None:
        """Serialize and save the field value to a file.

        This abstract method must be implemented by subclasses to define how data
        is serialized and written to the file. It is called automatically when
        the Resource is saved.

        The data MUST be written to the exact file path provided. The directory
        containing the file is guaranteed to exist.

        :param r_field_value: The field value to serialize and save
        :type r_field_value: Any
        :param file_path: Absolute path where the data should be saved
        :type file_path: str

        Example:
            ```python
            def dump_to_file(self, r_field_value: pd.DataFrame, file_path: str) -> None:
                r_field_value.to_csv(file_path, index=False)
            ```
        """
