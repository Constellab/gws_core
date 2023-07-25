# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from abc import abstractmethod
from typing import Type

from gws_core.resource.resource import Resource


class IOValidator(object):
    """
    IO Validator
    """

    resource_type: Type[Resource] = Resource

    def check_type(self, resource: Resource) -> None:
        """
        Check if resource type is valid
        """
        if not isinstance(resource, self.resource_type):
            raise Exception(
                f"Resource type '{resource.__class__.__name__}' is not valid. Expected '{self.resource_type.__name__}'")

    @abstractmethod
    def validate(self, resource: Resource) -> None:
        """
        Validate data
        """
