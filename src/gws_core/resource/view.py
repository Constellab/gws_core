# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, List, Optional

from pandas import DataFrame

from ..config.config_types import ConfigParams
from .view_types import ViewSpecs


class View:

    _type: str = 'view'
    _title: str = ''
    _caption: str = ''

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

    def set_title(self, title: str):
        """ Set title """
        self._title = title

    def set_caption(self, caption: str):
        """ Set caption """
        self._caption = caption

    def to_dict(self, params: ConfigParams) -> dict:
        """ Convert to dictioannry """
        return {
            "type": self._type,
            "title": self._title,
            "caption": self._caption,
        }

    @classmethod
    def json_is_from_view(cls, json_: Any) -> bool:
        """
        Method that return true is the provided json is a json of a view
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

    @classmethod
    def list_to_float(cls, list_: List[Any], remove_none: bool = False) -> List[Optional[float]]:
        """Convert a list of any to list of float. The element that
        are not convertible to float are set to None

        :param list_: _description_
        :type list_: List[Any]
        :param remove_none: if False, the non converted element are keep as None,
                            if True they are removed
        :type remove_none: List[Any]
        :return: _description_
        :rtype: List[Optional[float]]
        """
        data = [cls.to_float(val) for val in list_]

        if remove_none:
            return [i for i in data if i is not None]
        return data

    @classmethod
    def dataframe_to_float(cls, dataframe: DataFrame) -> DataFrame:
        """Convert all element of a dataframe to float, if element is not convertible, is sets Nan
        """
        return dataframe.applymap(cls.to_float,  na_action='ignore')

    @classmethod
    def to_float(cls, value: Any) -> Optional[float]:
        """Convert any to list of float. If not convertible to float, returns None
        """
        try:
            return float(value)
        except:
            return None

    @classmethod
    def generate_range(cls, length: int) -> List[int]:
        """Generate range list like 0,1,2...length
        """
        return list(range(0, length))

    @classmethod
    def flatten_dataframe_by_column(cls, dataframe: DataFrame) -> List[Any]:
        """Flatten a 2d data to a list of value. The values are added by column
        """
        values: List[Any] = []
        # flatten columns into values list
        for column in dataframe:
            values += dataframe[column].to_list()

        return values
