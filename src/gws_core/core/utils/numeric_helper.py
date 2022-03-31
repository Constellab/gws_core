# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, List, Optional

from numpy import isnan


class NumericHelper():
    """Helper to manipulate numerics
    """

    @staticmethod
    def list_to_float(list_: List[Any], remove_none: bool = False) -> List[Optional[float]]:
        """Convert a list of any to list of float.

        :param list_: _description_
        :type list_: List[Any]
        :param remove_none: if False, the non converted element are keep as None,
                            if True they are removed
        :type remove_none: List[Any]
        :return: _description_
        :rtype: List[Optional[float]]
        """
        data = [NumericHelper.to_float(val) for val in list_]

        if remove_none:
            return [i for i in data if i is not None]
        return data

    @staticmethod
    def to_float(value: Any) -> Optional[float]:
        """Convert any to float. If not convertible to float or NaN, returns None
        """
        if isnan(value):
            return None

        try:
            return float(value)
        except:
            return None

    @staticmethod
    def list_to_int(list_: List[Any], remove_none: bool = False) -> List[Optional[int]]:
        """Convert a list of any to list of int.
        :param list_: _description_
        :type list_: List[Any]
        :param remove_none: if False, the non converted element are keep as None,
                            if True they are removed
        :type remove_none: List[Any]
        :return: _description_
        :rtype: List[Optional[float]]
        """
        data = [NumericHelper.to_int(val) for val in list_]

        if remove_none:
            return [i for i in data if i is not None]
        return data

    @staticmethod
    def to_int(value: Any) -> Optional[int]:
        """Convert any to int. If not convertible to int or NaN, returns None
        """
        if isnan(value):
            return None

        try:
            return int(value)
        except:
            return None

    @staticmethod
    def to_int(value: Any) -> Optional[int]:
        """Convert any to int. If not convertible to int, returns None
        """
        try:
            return int(value)
        except:
            return None
