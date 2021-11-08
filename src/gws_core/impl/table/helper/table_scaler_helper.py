# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

import numpy
import pandas
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException


class TableScalerHelper:

    VALID_SCALING_FUNCTIONS = ["none", "log2", "log10"]

    @classmethod
    def _check_func(cls, func):
        if func not in cls.VALID_SCALING_FUNCTIONS:
            raise BadRequestException(
                f"The scaling function '{func}' is not valid. Valid scaling functions are {cls.VALID_SCALING_FUNCTIONS}."
            )

    @classmethod
    def scale(
            cls, data: DataFrame, func: str) -> DataFrame:
        cls._check_func(func)

        def _log10(x):
            return numpy.log10(x) if isinstance(x, (float, int,)) else numpy.NaN

        def _log2(x):
            return numpy.log2(x) if isinstance(x, (float, int,)) else numpy.NaN

        if func and func != "none":
            if func == "log10":
                data = data.applymap(_log10, na_action='ignore')
            elif func == "log2":
                data = data.applymap(_log2, na_action='ignore')
        return data
