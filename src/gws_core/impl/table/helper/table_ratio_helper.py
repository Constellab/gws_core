# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.table.table import Table


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
