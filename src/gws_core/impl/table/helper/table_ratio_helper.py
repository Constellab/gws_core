# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from re import split, sub
from typing import List, Union

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.table.table import Table
from pandas import DataFrame


class TableRatioHelper():

    OPERATION_SEPARATOR: str = '\n'

    @staticmethod
    def columns_ratio(source: Table, operations: Union[str, List[str]], result_in_new_column: bool) -> Table:

        # convert the operations to str
        if isinstance(operations, list):
            operations = TableRatioHelper.OPERATION_SEPARATOR.join(operations)

        dataframe = source.get_data()

        if result_in_new_column:
            if '=' in operations:
                raise BadRequestException("The operation cannot contain '=' if the result is set in a new column")
            column_name = source.generate_new_column_name('Result')
            operations = f"{column_name} = {operations}"

        eval_dataframe = dataframe.eval(operations)
        result_table: Table

        # if the result is append to the dataframe
        if '=' in operations:
            # get a copy of the dataframe
            result_table = Table(dataframe.copy())

            # add calculated column to the dataframe
            index = 0
            for column in eval_dataframe:
                if not result_table.column_exists(column):
                    result_table.add_column(column, eval_dataframe[column], index)
                    index += 1
        else:
            # create a Table with only calculated columns
            result_table = Table(eval_dataframe)

        result_table.copy_row_tags(source)
        return result_table

    @staticmethod
    def rows_ratio(source: Table, operations: Union[str, List[str]], result_in_new_row: bool) -> Table:
        t_table = source.transpose()
        result_transposed = TableRatioHelper.columns_ratio(t_table, operations, result_in_new_row)
        return result_transposed.transpose()

    @staticmethod
    def columns_ratio_from_table(table: Table, ratio_df: DataFrame,
                                 ratio_name_column: str = None, ratio_operation_column: str = None,
                                 error_on_unknown_column: bool = False) -> Table:
        """Call multiple ratio on table, the ratios must be sto

        :param table: _description_
        :type table: Table
        :param ratio_df: _description_
        :type ratio_df: DataFrame
        :param ratio_name_column: name of the column that contains ratio name(take first column if none), defaults to None
        :type ratio_name_column: str, optional
        :param ratio_operation_column: name of the column that contains operation (take second column if none), defaults to None
        :type ratio_operation_column: str, optional
        :param error_on_unknown_column: If False, the unknow column are replace with 0, if true nothin is done, defaults to None
        :type error_on_unknown_column: str, optional
        :return: _description_
        :rtype: Table
        """
        operations: List[str] = []

        if ratio_df.shape[1] < 2:
            raise Exception(
                "The ratio table must have at least 2 columns")

        # check ratio_name_column
        if ratio_name_column is None:
            ratio_name_column = 0
        else:
            if ratio_name_column not in ratio_df.columns:
                raise Exception(
                    f"The ratio name column '{ratio_name_column}' does not exist in the ratio table")

        # check ratio_operation_column
        if ratio_operation_column is None:
            ratio_operation_column = 1
        else:
            if ratio_operation_column not in ratio_df.columns:
                raise Exception(
                    f"The ratio operation column '{ratio_operation_column}' does not exist in the ratio table")

        for index, row in ratio_df.iterrows():
            operation: str = str(row[ratio_operation_column])

            # if we throw an error if the column is unknown, do touch the operation
            if error_on_unknown_column:
                clean_operation = operation
            else:
                # remove the unknown columns
                clean_operation = TableRatioHelper._clean_operation_unknown_columns(operation, table)

            # create the operation
            operations.append(f"{row[ratio_name_column]} = {clean_operation}")

        return TableRatioHelper.columns_ratio(table, operations, False)

    @staticmethod
    def _clean_operation_unknown_columns(operation: str, table: Table) -> str:
        """ Replace the unknown column name with '0' in the operation"""
        clean_operation = StringHelper.remove_whitespaces(operation)

        # split by all basic operator : +,-,*,/,^,(,),>,<,= to check column name
        column_names = split('\+|-|/|\*|\(|\)|\%|\^|>|<|=', clean_operation)
        column_names = [x for x in column_names if x]

        # check if the column name is in the table or a float
        for column_name in column_names:

            # if the element is a number, skip it
            column_int = NumericHelper.to_float(column_name)
            if column_int is not None:
                continue

            # check if the column name exist and if not, replace it with '0'
            if column_name not in table.column_names:
                # replace the column name with '0' using \b to word delimiter
                clean_operation = sub(rf'\b{column_name}\b', '0', clean_operation)

        return clean_operation
