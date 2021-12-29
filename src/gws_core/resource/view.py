# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any

from ..config.config_types import ConfigParams
from .view_types import ViewSpecs


class View:

    _type: str = 'view'

    # Spec of the view. All the view spec must be optional or have a default value
    _specs: ViewSpecs = {}

    def __init__(self, *args, **kwargs):
        self._check_view_specs()

    def _check_view_specs(self) -> None:
        """This method checks that the view specs are ok

        :raises Exception: [description]
        """
        if self._specs is None:
            return

        for key, spec in self._specs.items():
            if not spec.optional:
                raise Exception(
                    f"The spec '{key}' of the view '{self.__class__.__name__}' is not optional. All the view specs must be optional or have a default value")

    def to_dict(self, params: ConfigParams) -> dict:
        return {
            "type": self._type,
        }

    @classmethod
    def json_is_from_view(cls, json_: Any) -> bool:
        """Method that return true is the provided json is a json of a view
        """

        if json_ is None or not isinstance(json_, dict):
            return False

        # check type
        if "type" not in json_ or json_["type"] is None or not isinstance(json_["type"], str):
            return False

        # Check data
        if "data" not in json_ or json_["data"] is None:
            return False

        return True
