from re import sub
from typing import Any

from numpy import NaN, inf
from numpy.ma import masked
from pandas import DataFrame

from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.core.utils.utils import Utils


class DataframeHelper:
    CSV_DELIMITERS: list[str] = ["\t", ",", ";"]
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
            if count > max_delimiter_count:
                max_delimiter = delimiter
                max_delimiter_count = count

        return max_delimiter

    @staticmethod
    def flatten_dataframe_by_column(dataframe: DataFrame) -> list[Any]:
        """Flatten a 2d data to a list of value. The values are added by column"""
        values: list[Any] = []
        # flatten columns into values list
        for column in dataframe:
            values += dataframe[column].to_list()

        return values

    @staticmethod
    def dataframe_to_float(dataframe: DataFrame) -> DataFrame:
        """Convert all element of a dataframe to float, if element is not convertible, is sets NaN"""
        return dataframe.map(lambda x: NumericHelper.to_float(x, NaN), na_action="ignore")

    @classmethod
    def replace_inf(cls, data: DataFrame, value=NaN) -> DataFrame:
        return data.replace([inf, -inf], value)

    @classmethod
    def prepare_to_json(cls, dataframe: DataFrame, value: Any) -> DataFrame:
        """
        Convert all weird values (like NaN, inf, masked) to value to be able to convert to json
        """
        data: DataFrame = dataframe.replace({NaN: value})
        # replace masked value by value
        data = data.map(lambda x: value if x is masked else x, na_action="ignore")
        return cls.replace_inf(data, value)

    @classmethod
    def nanify_none_number(cls, data: DataFrame) -> DataFrame:
        """Convert all not numeric element to NaN"""
        return data.map(lambda x: x if isinstance(x, (float, int)) else NaN)

    @classmethod
    def nanify_none_str(cls, data: DataFrame) -> DataFrame:
        """Convert all not string element to NaN"""
        return data.map(lambda x: x if isinstance(x, str) else NaN)

    @classmethod
    def contains(cls, data: DataFrame, value: Any) -> DataFrame:
        """
        Return a dataframe with True if the cell contains the value
        """
        return data.map(lambda x: value in x, na_action="ignore")

    @classmethod
    def contains_not(cls, data: DataFrame, value: Any) -> DataFrame:
        """
        Return a dataframe with True if the cell does not contain the value
        """
        return data.map(lambda x: value not in x, na_action="ignore")

    @classmethod
    def starts_with(cls, data: DataFrame, value: str) -> DataFrame:
        """
        Return a dataframe with True if the cell starts with the value
        """
        return data.map(lambda x: x.startswith(value), na_action="ignore")

    @classmethod
    def ends_with(cls, data: DataFrame, value: str) -> DataFrame:
        """
        Return a dataframe with True if the cell ends with the value
        """
        return data.map(lambda x: x.endswith(value), na_action="ignore")

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
    def format_column_and_row_names(cls, data: DataFrame, strict: bool = False) -> DataFrame:
        """
        Format the columns and row names and remove duplicate names
        """
        data.columns = cls.format_header_names(data.columns, strict)
        data.index = cls.format_header_names(data.index, strict)
        return cls.rename_duplicate_column_and_row_names(data)

    @classmethod
    def format_header_names(cls, names: list[Any], strict: bool = False) -> list[str]:
        """Format the names of a row or a column with the following rules:
        - convert to string

        If strict is True, the following rules are applied:
        - replace ' ', '-', '.' with underscores
        - remove all other special characters
        - remove all accents
        """

        return [cls.format_header_name(name, strict) for name in names]

    @classmethod
    def format_header_name(cls, name: str, strict: bool = False) -> str:
        """Format the names of a row or a column with the following rules:
        - convert to string
        - trim

        If strict is True, the following rules are applied:
        - replace ' ', '-', '.' with underscores
        - remove all other special characters
        - remove all accents
        """
        if name is None:
            return ""

        str_name = str(name)
        str_name = str_name.strip()

        if strict:
            # with regex replace all spaces, dashes and dots with underscores
            str_name = sub(r"[\s.-]+", "_", str_name)
            str_name = StringHelper.replace_accent_with_letter(str_name)
            str_name = sub("[^A-Za-z0-9_]+", "", str_name)
        return str_name
