
from abc import abstractmethod
from typing import Any

from .view_types import ViewSpecs


class View:

    _type: str = 'view'

    # Spec of the view. All the view spec must be optional or have a default value
    _specs: ViewSpecs = None
    _data: Any

    def __init__(self, data: Any):
        self._data = self.check_and_clean_data(data)
        self.__check_view_specs()

    def __check_view_specs(self) -> None:
        """This method checks that the view specs are ok

        :raises Exception: [description]
        """
        if self._specs is None:
            return

        for key, spec in self._specs.items():
            if not spec.optional:
                raise Exception(
                    f"The spec '{key}' of the view '{self.__class__.__name__}' is not optional. All the view spec must be optional or have a default value")

    def check_and_clean_data(self, data):
        """
        Check the data and return.

        Must be overloaded to implement adhoc data checker
        """

        return data

    @abstractmethod
    def to_dict(self, **kwargs) -> dict:
        pass
