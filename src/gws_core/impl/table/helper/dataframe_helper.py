# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from cmath import inf
from typing import Any, List

from gws_core.core.utils.numeric_helper import NumericHelper
from numpy import NaN, inf
from pandas import DataFrame


class DataframeHelper:

    CSV_DELIMITERS: List[str] = ['\t', ',', ';']
    DEFAULT_CSV_DELIMITER = ","

    @staticmethod
    def detect_csv_delimiter(csv_str: str) -> str:
        """
        Method to guess the delimiter of a csv string based on delimiter count.

        By default, the delimiter is comma.
        """
        if csv_str is None or len(csv_str) < 10:
            return None

        max_delimiter: str = DataframeHelper.DEFAULT_CSV_DELIMITER
        max_delimiter_count: int = 0

        # use a sub csv to improve speed
        sub_csv = csv_str[0:10000]

        for delimiter in DataframeHelper.CSV_DELIMITERS:
            count: int = sub_csv.count(delimiter)
            if(count > max_delimiter_count):
                max_delimiter = delimiter
                max_delimiter_count = count

        return max_delimiter

    @staticmethod
    def flatten_dataframe_by_column(dataframe: DataFrame) -> List[Any]:
        """Flatten a 2d data to a list of value. The values are added by column
        """
        values: List[Any] = []
        # flatten columns into values list
        for column in dataframe:
            values += dataframe[column].to_list()

        return values

    @staticmethod
    def dataframe_to_float(dataframe: DataFrame) -> DataFrame:
        """Convert all element of a dataframe to float, if element is not convertible, is sets Nan
        """
        return dataframe.applymap(NumericHelper.to_float,  na_action='ignore')

    @classmethod
    def nanify(cls, data: DataFrame) -> DataFrame:
        return data.applymap(cls._nanify_value, na_action='ignore')

    @classmethod
    def replace_inf(cls, data: DataFrame, value=NaN) -> DataFrame:
        return data.replace([inf, -inf], value)

    @staticmethod
    def _nanify_value(x):
        return x if isinstance(x, (float, int,)) else NaN
