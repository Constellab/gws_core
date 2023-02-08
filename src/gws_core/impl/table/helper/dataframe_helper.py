# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from cmath import inf
from re import sub
from typing import Any, List

from numpy import inf
from numpy import nan as np_nan
from pandas import NA, DataFrame

from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.core.utils.utils import Utils


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
            if (count > max_delimiter_count):
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
        """Convert all element of a dataframe to float, if element is not convertible, is sets NA
        """
        return dataframe.applymap(lambda x: NumericHelper.to_float(x, NA),  na_action='ignore')

    @classmethod
    def replace_inf(cls, data: DataFrame, value=NA) -> DataFrame:
        return data.replace([inf, -inf], value)

    @classmethod
    def replace_nan_and_inf(cls, dataframe: DataFrame, value: Any) -> DataFrame:
        data: DataFrame = dataframe.replace({NA: value})
        return cls.replace_inf(data, value)

    @classmethod
    def nanify_none_numeric(cls, data: DataFrame) -> DataFrame:
        """ Convert all not numeric element to NA"""
        return data.applymap(lambda x: x if isinstance(x, (float, int)) else NA,
                             na_action='ignore')

    @classmethod
    def nanify_none_str(cls, data: DataFrame) -> DataFrame:
        """ Convert all not string element to NA"""
        return data.applymap(lambda x: x if isinstance(x, str) else NA,
                             na_action='ignore')

    @classmethod
    def contains(cls, data: DataFrame, value: Any) -> DataFrame:
        """
        Return a dataframe with True if the cell contains the value
        """
        return data.applymap(lambda x: value in x, na_action='ignore')

    @classmethod
    def contains_not(cls, data: DataFrame, value: Any) -> DataFrame:
        """
        Return a dataframe with True if the cell does not contain the value
        """
        return data.applymap(lambda x: value not in x, na_action='ignore')

    @classmethod
    def starts_with(cls, data: DataFrame, value: str) -> DataFrame:
        """
        Return a dataframe with True if the cell starts with the value
        """
        return data.applymap(lambda x: x.startswith(value), na_action='ignore')

    @classmethod
    def ends_with(cls, data: DataFrame, value: str) -> DataFrame:
        """
        Return a dataframe with True if the cell ends with the value
        """
        return data.applymap(lambda x: x.endswith(value), na_action='ignore')

    @classmethod
    def stringify(cls, data: DataFrame) -> DataFrame:
        """
        Convert all element of a dataframe to string
        """
        return data.astype(str)

    @classmethod
    def rename_duplicate_column_and_row_names(cls, data: DataFrame) -> DataFrame:
        """
        Rename duplicate columns and rows name by addind _1 ,_2 ... at the end of the name
        """
        data = cls.rename_duplicate_column_names(data)
        data = cls.rename_duplicate_row_names(data)
        return data

    @classmethod
    def rename_duplicate_column_names(cls, data: DataFrame) -> DataFrame:
        """
        Rename duplicate columns name by addind _1 ,_2 ... at the end of the name
        """
        renamed_columns = Utils.rename_duplicate_in_str_list(data.columns.to_list())
        data.columns = renamed_columns
        return data

    @classmethod
    def rename_duplicate_row_names(cls, data: DataFrame) -> DataFrame:
        """
        Rename duplicate rows  by addind _1 ,_2 ... at the end of the name
        """
        renamed_rows = Utils.rename_duplicate_in_str_list(data.index.to_list())
        data.index = renamed_rows
        return data

    @classmethod
    def format_column_and_row_names(cls, data: DataFrame) -> DataFrame:
        """
        Format the columns and row names and remove duplicate names
        """
        data.columns = cls.format_header_names(data.columns)
        data.index = cls.format_header_names(data.index)
        return cls.rename_duplicate_column_and_row_names(data)

    @classmethod
    def format_header_names(cls, names: List[Any]) -> List[str]:
        """Format the names of a row or a column with the following rules:
          - convert to string
          - replace ' ', '-', '.' with underscores
          - remove all other special characters
          - remove all accents
          - convert to lower case
        """

        return [cls.format_header_name(name) for name in names]

    @classmethod
    def format_header_name(cls, name: str) -> str:
        """Format the name of a row or a column with the following rules:
          - convert to string
          - replace ' ', '-', '.' with underscores
          - remove all other special characters
          - remove all accents
          - if start with a number, add an underscore at the beginning
        """
        if name is None:
            return ''

        str_name: str = str(name)
        # with regex replace all spaces, dashes and dots with underscores
        str_name = sub(r'[\s.-]+', '_', str_name)
        str_name = StringHelper.replace_accent_with_letter(str_name)
        str_name = sub('[^A-Za-z0-9_]+', '', str_name)
        if str_name[0].isdigit():
            str_name = '_' + str_name
        return str_name

    @classmethod
    def replace_numpy_nan_with_pandas_nan(cls, data: DataFrame) -> DataFrame:
        """
        Replace all numpy nan with pandas nan
        """
        return data.replace(np_nan, NA)
