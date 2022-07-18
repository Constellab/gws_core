# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import numpy
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException


class DataframeScalerHelper:

    VALID_SCALING_FUNCTIONS = ["none", "log", "log2", "log10", "unit", "percent", "standard"]

    @classmethod
    def _check_func(cls, func):
        if func not in cls.VALID_SCALING_FUNCTIONS:
            raise BadRequestException(
                f"The scaling function '{func}' is not valid. Valid scaling functions are {cls.VALID_SCALING_FUNCTIONS}."
            )

    @classmethod
    def scale(
            cls, data: DataFrame, func: str) -> DataFrame:
        if func is None or func == "none":
            return data
        cls._check_func(func)

        if func == "log10":
            data = data.applymap(DataframeScalerHelper._log10, na_action='ignore')
        elif func == "log2":
            data = data.applymap(DataframeScalerHelper._log2, na_action='ignore')
        elif func == "log":
            data = data.applymap(DataframeScalerHelper._log, na_action='ignore')
        else:
            data = DataframeHelper.nanify(data)
            if func == "unit":
                data = data / data.sum(skipna=None)
            elif func == "percent":
                data = (data / data.sum(skipna=None)) * 100
            elif func == "standard":
                data = (data - data.mean(skipna=True)) / data.std(skipna=None)

        return data

    @staticmethod
    def _log10(x):
        return numpy.log10(x) if isinstance(x, (float, int,)) else numpy.NaN

    @staticmethod
    def _log2(x):
        return numpy.log2(x) if isinstance(x, (float, int,)) else numpy.NaN

    @staticmethod
    def _log(x):
        return numpy.log(x) if isinstance(x, (float, int,)) else numpy.NaN
