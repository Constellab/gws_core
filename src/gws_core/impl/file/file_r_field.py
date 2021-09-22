from abc import abstractmethod
from typing import Any, final

from ...resource.r_field import BaseRField


class FileRField(BaseRField):
    """ Abstract class that must be extended to define RField that are dump and load directly into a file
    """

    def __init__(self,
                 default_value: Any = None) -> None:
        super().__init__(searchable=False,
                         default_value=default_value, include_in_dict_view=False)

    @final
    def deserialize(self, r_field_value: str) -> Any:
        return self.load_from_file(r_field_value)

    @final
    def serialize(self, r_field_value: Any) -> str:
        """
        METHOD NOT USED
        """

    @abstractmethod
    def load_from_file(self, file_path: str) -> Any:
        """Implement this method to load your object from the file

        :param file_path: path of the file
        :type file_path: str
        :return: loaded object
        :rtype: Any
        """

    @abstractmethod
    def dump_to_file(self, r_field_value: Any, file_path: str) -> None:
        """Implement this method to dump your object into a file to ba able
        to load it later

        :param r_field_value: object to dump (value of the r_field)
        :type r_field_value: Any
        :param file_path: path of the file to dump (the object MUST be dumped into this file)
        :type file_path: str
        """
