# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Literal

import numpy
from pandas import DataFrame

from gws_core.core.utils.utils import Utils
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper

from ....core.exception.exceptions import BadRequestException

DfScaleFunction = Literal["none", "log", "log2", "log10"]
DfAxisScaleFunction = Literal["unit", "percent", "standard"]


class DataframeScalerHelper:

    SCALE_FUNCTIONS = Utils.get_literal_values(DfScaleFunction)
    AXIS_SCALE_FUNCTIONS = Utils.get_literal_values(DfAxisScaleFunction)

    @classmethod
    def scale(
            cls, data: DataFrame, func: DfScaleFunction) -> DataFrame:
        cls._check_scale_func(func)

        if func == "log10":
            data = data.applymap(DataframeScalerHelper._log10, na_action='ignore')
        elif func == "log2":
            data = data.applymap(DataframeScalerHelper._log2, na_action='ignore')
        elif func == "log":
            data = data.applymap(DataframeScalerHelper._log, na_action='ignore')

        return data

    @classmethod
    def scale_by_columns(cls, data: DataFrame, func: DfAxisScaleFunction) -> DataFrame:
        result = DataframeHelper.nanify_none_number(data)

        if func == "unit":
            result = result / result.sum(skipna=True)
        elif func == "percent":
            result = (result / result.sum(skipna=True)) * 100
        elif func == "standard":
            result = (result - result.mean(skipna=True)) / result.std(skipna=True)

        return result

    @classmethod
    def scale_by_rows(cls, data: DataFrame, func: DfAxisScaleFunction) -> DataFrame:
        return cls.scale_by_columns(data.T, func).T

    @staticmethod
    def _log10(x):
        return numpy.log10(x) if isinstance(x, (float, int,)) else numpy.NaN

    @staticmethod
    def _log2(x):
        return numpy.log2(x) if isinstance(x, (float, int,)) else numpy.NaN

    @staticmethod
    def _log(x):
        return numpy.log(x) if isinstance(x, (float, int,)) else numpy.NaN

    @classmethod
    def _check_scale_func(cls, func: DfScaleFunction):
        if not Utils.value_is_in_literal(func, DfScaleFunction):
            raise BadRequestException(
                f"The scaling function '{func}' is not valid. Valid scaling functions are {Utils.get_literal_values(DfScaleFunction)}."
            )

    @classmethod
    def _check_axis_scale_func(cls, func: DfAxisScaleFunction):
        if not Utils.value_is_in_literal(func, DfAxisScaleFunction):
            raise BadRequestException(
                f"The axis scaling function '{func}' is not valid. Valid axis scaling functions are {Utils.get_literal_values(DfAxisScaleFunction)}."
            )
