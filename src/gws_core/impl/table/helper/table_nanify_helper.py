# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

import numpy
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException
from .table_aggregator_helper import TableAggregatorHelper


class TableNanifyHelper:
    """
        Nanify a DataFrame ,i.e. replace all non numeric values by NaN. Only `float` and `int` are checked
    """
    @classmethod
    def nanify(cls, data: DataFrame) -> DataFrame:
        return data.applymap(cls._nanify_value, na_action='ignore')

    @staticmethod
    def _nanify_value(x):
        return x if isinstance(x, (float, int,)) else numpy.NaN