# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import numpy
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException
from .table_nanify_helper import TableNanifyHelper

class TableScalerHelper:

    VALID_SCALING_FUNCTIONS = ["none", "log2", "log10", "unit", "percent", "standard"]

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
            data = data.applymap(TableScalerHelper._log10, na_action='ignore')
        elif func == "log2":
            data = data.applymap(TableScalerHelper._log2, na_action='ignore')
        else:
            data = TableNanifyHelper.nanify(data)
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
