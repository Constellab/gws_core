

from enum import Enum
from re import split, sub
from typing import List

from numpy import NaN
from pandas import DataFrame

from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.table.table import Table

from ....core.utils.utils import Utils


class TableOperationUnknownColumnOption(Enum):
    """Options for unknown column in operation"""

    # Throw an error if the column is unknown
    ERROR = 'Error'
    # Set the result to NaN if 1 column is unknown
    SET_RESULT_TO_NAN = 'Set result to NaN'
    # Replace the unknown columns with 0
    REPLACE_WITH_0 = 'Replace unknown columns with 0'


class TableOperationHelper():

    # custom str to set NaN on eval, the string is then replace with real NaN
    _NaN_str = '__NaN__'

    OPERATION_SEPARATOR: str = '\n'

    @staticmethod
    def column_operations(source: Table, operations: List[str], keep_original_columns: bool) -> Table:

        if not isinstance(operations, list):
            raise Exception('The operations must be a list')

        clean_operations: List[str] = []
        column_names = source.column_names
        for operation in operations:
            if '=' in operation:
                clean_operations.append(operation)
            else:
                column_name = Utils.generate_unique_str_for_list(column_names, 'Result')
                clean_operations.append(f"{column_name} = {operation}")
                # append the new column name to the list of column names to avoid duplicates 'Result' columns
                column_names.append(column_name)

        # convert the operations to str
        str_operation: str = TableOperationHelper.OPERATION_SEPARATOR.join(clean_operations)

        dataframe = source.get_data()

        eval_dataframe: DataFrame = dataframe.eval(str_operation, engine='python')
        eval_dataframe = eval_dataframe.replace(TableOperationHelper._NaN_str, NaN)
        result_table: Table

        # if the result is append to the dataframe
        if keep_original_columns:
            # get a copy of the dataframe
            result_table = Table(dataframe.copy())

            # add calculated column to the dataframe
            index = 0
            for column in eval_dataframe:
                if not result_table.column_exists(column):
                    result_table.add_column(column, eval_dataframe[column], index)
                    index += 1
        else:
            result_table = Table()
            for column in eval_dataframe:
                if not column in dataframe:
                    result_table.add_column(column, eval_dataframe[column])

            # set the row names as the table was created empty
            result_table.set_all_row_names(source.row_names)

        result_table.copy_row_tags_by_index(source)
        return result_table

    @staticmethod
    def row_operation(source: Table, operations: List[str], keep_original_rows: bool) -> Table:
        t_table = source.transpose()
        result_transposed = TableOperationHelper.column_operations(t_table, operations, keep_original_rows)
        return result_transposed.transpose(infer_objects=True)

    @staticmethod
    def column_mass_operations(
            table: Table, operation_df: DataFrame, operation_name_column: str = None,
            operation_calculations_column: str = None,
            replace_unknown_column: TableOperationUnknownColumnOption = TableOperationUnknownColumnOption.SET_RESULT_TO_NAN,
            keep_original_columns: bool = False) -> Table:
        """Call multiple operations on table, the operations must be stored in a DataFrame.

        :param table: _description_
        :type table: Table
        :param operation_df: _description_
        :type operation_df: DataFrame
        :param operation_name_column: name of the column that contains the operations' names(takes first column if none), defaults to None
        :type operation_name_column: str, optional
        :param operation_column: name of the column that contains operation (takes second column if none), defaults to None
        :type operation_column: str, optional
        :param replace_unknown_column: Option to handle unknown columns, defaults to False
        :type replace_unknown_column: TableOperationUnknownColumnOption, optional
        :param keep_original_columns: If True, the original columns used for the calculations are added at the end of the table.
                                      Otherwise, only the calculated columns are kept, defaults to False
        :type keep_original_columns: str, optional
        :return: _description_
        :rtype: Table
        """
        operations: List[str] = []

        if operation_df.shape[1] < 2:
            raise Exception(
                "The operation table must have at least 2 columns")

        # check operation_name_column
        if not operation_name_column:
            operation_name_column = 0
        else:
            if operation_name_column not in operation_df.columns:
                raise Exception(
                    f"The operation name column '{operation_name_column}' does not exist in the operation table, please check your configuration")

        # check operation_column
        if not operation_calculations_column:
            operation_calculations_column = 1
        else:
            if operation_calculations_column not in operation_df.columns:
                raise Exception(
                    f"The operation operation column '{operation_calculations_column}' does not exist in the operation table, please check your configuration")

        for _, row in operation_df.iterrows():
            operation: str = str(row.iloc[operation_calculations_column])

            # if we throw an error if the column is unknown, don't touch the operation
            if replace_unknown_column == TableOperationUnknownColumnOption.ERROR:
                clean_operation = operation
            elif replace_unknown_column == TableOperationUnknownColumnOption.SET_RESULT_TO_NAN:
                if TableOperationHelper._operation_contains_unknown_column(operation, table):
                    clean_operation = f"'{TableOperationHelper._NaN_str}'"
                else:
                    clean_operation = operation
            else:
                # remove the unknown columns
                clean_operation = TableOperationHelper._clean_operation_unknown_columns(operation, table)

            # create the operation
            operations.append(f"{row.iloc[operation_name_column]} = {clean_operation}")

        return TableOperationHelper.column_operations(table, operations, keep_original_columns)

    @staticmethod
    def _operation_contains_unknown_column(operation: str, table: Table) -> bool:
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
                return True

        return False

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

        # replace +0 and -0 with empty string to lighten the operation
        clean_operation = sub('\+0|\-0', '', clean_operation)
        return clean_operation
