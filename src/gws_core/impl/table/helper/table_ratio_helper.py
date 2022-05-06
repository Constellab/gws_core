# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.table.table import Table


class TableRatioHelper():

    @staticmethod
    def columns_ratio(source: Table, operation: str, result_in_new_column: bool) -> Table:
        dataframe = source.get_data()

        if result_in_new_column:
            if '=' in operation:
                raise BadRequestException("The operation cannot contain '=' if the result is set in a new column")
            column_name = source.generate_new_column_name('Result')
            operation = f"{column_name} = {operation}"

        eval_dataframe = dataframe.eval(operation)
        result_table: Table

        # if the result is append to the dataframe
        if '=' in operation:
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
    def rows_ratio(source: Table, operation: str, result_in_new_row: bool) -> Table:
        t_table = source.transpose()
        result_transposed = TableRatioHelper.columns_ratio(t_table, operation, result_in_new_row)
        return result_transposed.transpose()
