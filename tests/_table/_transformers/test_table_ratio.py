# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import IsolatedAsyncioTestCase

from gws_core import Table
from gws_core.impl.table.helper.table_ratio_helper import TableRatioHelper
from pandas import DataFrame


class TestTableRatio(IsolatedAsyncioTestCase):

    def test_table_column_ratio(self):
        dataframe = DataFrame({'A': range(1, 6), 'B': [10, 8, 6, 4, 2]})

        table = Table(data=dataframe)

        result_table = TableRatioHelper.columns_ratio(table, 'A + B', False)
        expected_result = DataFrame({0: [11, 10, 9, 8, 7]})
        self.assertTrue(result_table.get_data().equals(expected_result))

        result_table = TableRatioHelper.columns_ratio(table, 'A + B', True)
        expected_result = DataFrame({'Result': [11, 10, 9, 8, 7], 'A': range(1, 6), 'B': [10, 8, 6, 4, 2]})
        self.assertTrue(result_table.get_data().equals(expected_result))

    # def test_table_row_ratio(self):
    #     dataframe = DataFrame({'A': range(1, 6), 'B': [10, 8, 6, 4, 2]})

    #     table = Table(data=dataframe)

    #     result_table = TableRatioHelper.call_row_ratio(table, '0 + 1', False)
    #     expected_result = DataFrame({'0': [11, 10, 9, 8, 7]})
    #     self.assertTrue(result_table.get_data().equals(expected_result))

    #     result_table = TableRatioHelper.call_row_ratio(table, 'A + B', True)
    #     expected_result = DataFrame({'A': range(1, 6), 'B': [10, 8, 6, 4, 2], 'Result': [11, 10, 9, 8, 7]})
    #     self.assertTrue(result_table.get_data().equals(expected_result))

    def test_table_column_ratio_from_table(self):
        dataframe = DataFrame({'A': [1, 2, 3], 'B': [10, 8, 6], 'C': [7, 1, 5]})

        table = Table(data=dataframe)

        # Test simple ratio
        ratio_dataframe = DataFrame({'Ratio_name': ['R0', 'R1'], 'Ratio': ['A + B', 'A - C']})

        # A + B and A - C
        result_table = TableRatioHelper.columns_ratio_from_table(table, ratio_dataframe)
        self.assertEqual(result_table.nb_columns, 5)
        self.assertEqual(list(result_table.get_data()['R0']), [11, 10, 9])
        self.assertEqual(list(result_table.get_data()['R1']), [-6, 1, -2])

        # Test with unknown column in ratio Z
        ratio_dataframe = DataFrame({'Ratio_name': ['R0'], 'Ratio': ['A + (Z - B) * 2']})

        result_table = TableRatioHelper.columns_ratio_from_table(table, ratio_dataframe)

        # The real operation will be A + (0 - B) * 2
        self.assertEqual(result_table.nb_columns, 4)
        self.assertEqual(list(result_table.get_data()['R0']), [-19, -14, 9])
