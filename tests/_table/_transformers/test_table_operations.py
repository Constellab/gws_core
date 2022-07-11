# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import IsolatedAsyncioTestCase

from gws_core import Table
from gws_core.impl.table.helper.table_operation_helper import \
    TableOperationHelper
from numpy import NaN, isnan
from pandas import DataFrame


class TestTableOperations(IsolatedAsyncioTestCase):

    def test_table_column_operations(self):
        dataframe = DataFrame({'A': range(1, 6), 'B': [10, 8, 6, 4, 2]})

        table = Table(data=dataframe)

        result_table = TableOperationHelper.column_operations(table, 'A + B', False)
        expected_result = DataFrame({0: [11, 10, 9, 8, 7]})
        self.assertTrue(result_table.get_data().equals(expected_result))

        result_table = TableOperationHelper.column_operations(table, 'A + B', True)
        expected_result = DataFrame({'Result': [11, 10, 9, 8, 7], 'A': range(1, 6), 'B': [10, 8, 6, 4, 2]})
        self.assertTrue(result_table.get_data().equals(expected_result))

    # def test_table_row_operation(self):
    #     dataframe = DataFrame({'A': range(1, 6), 'B': [10, 8, 6, 4, 2]})

    #     table = Table(data=dataframe)

    #     result_table = TableOperationHelper.call_row_operations(table, '0 + 1', False)
    #     expected_result = DataFrame({'0': [11, 10, 9, 8, 7]})
    #     self.assertTrue(result_table.get_data().equals(expected_result))

    #     result_table = TableOperationHelper.call_row_operations(table, 'A + B', True)
    #     expected_result = DataFrame({'A': range(1, 6), 'B': [10, 8, 6, 4, 2], 'Result': [11, 10, 9, 8, 7]})
    #     self.assertTrue(result_table.get_data().equals(expected_result))

    def test_table_column_mass_operations(self):
        dataframe = DataFrame({'A': [1, 2, 3], 'B': [10, 8, 6], 'C': [7, 1, 5]})

        table = Table(data=dataframe)

        # Test simple operation
        operation_df = DataFrame({'Operation_name': ['R0', 'R1'], 'Operation': ['A + B', 'A - C']})

        # A + B and A - C
        result_table = TableOperationHelper.column_mass_operations(table, operation_df)
        self.assertEqual(result_table.nb_columns, 5)
        self.assertEqual(list(result_table.get_data()['R0']), [11, 10, 9])
        self.assertEqual(list(result_table.get_data()['R1']), [-6, 1, -2])

        # Test with unknown column in operation Z
        operation_df = DataFrame({'Operation_name': ['R0'], 'Operation': ['A + (Z - B) * 2']})

        result_table = TableOperationHelper.column_mass_operations(table, operation_df)

        # The result should be NaN
        self.assertEqual(result_table.nb_columns, 4)
        # check if all element of R0 columns are NaN
        self.assertTrue(all(isnan(list(result_table.get_data()['R0']))))
