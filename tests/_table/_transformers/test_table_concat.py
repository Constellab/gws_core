# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from numpy import NaN
from pandas import DataFrame

from gws_core.impl.table.helper.table_concat_helper import TableConcatHelper
from gws_core.impl.table.table import Table
from gws_core.test.base_test_case import BaseTestCase


# test_table_concat
class TestTableConcat(TestCase):
    def test_table_row_concat_helper(self):

        df_1: DataFrame = DataFrame({'F1': [1, 2], 'F2': [7, 1]})
        row_tags_1 = [{'id': '1'}, {'id': '2'}]
        column_tags_1 = [{'id': 'F1'}, {'id': 'F2'}]
        table_1 = Table(df_1, row_tags=row_tags_1, column_tags=column_tags_1)

        df_2 = DataFrame({'F1': [4, 5], 'F3': [9, 8], 'F4': ['n1', 'n2']})
        row_tags_2 = [{'id': '3'}, {'id': '4'}]
        column_tags_2 = [{'id': 'F1', 'other': 'top'}, {'id': 'F3'}, {'id': 'F4'}]
        table_2 = Table(df_2, row_tags=row_tags_2, column_tags=column_tags_2)

        result: Table = TableConcatHelper.concat_table_rows(table_1, table_2,
                                                            column_tags_option='ignore', fill_nan=NaN)

        expected_df = DataFrame(
            {'F1': [1, 2, 4, 5],
             'F2': [7.0, 1.0, NaN, NaN],
             'F3': [NaN, NaN, 9.0, 8.0],
             'F4': [NaN, NaN, 'n1', 'n2']},
            index=['0', '1', '0_1', '1_1'])
        expected_row_tags = [{'id': '1'}, {'id': '2'}, {'id': '3'}, {'id': '4'}]
        self.assertTrue(DataFrame.equals(result.get_data(), expected_df))
        BaseTestCase.assert_json(result.get_row_tags(), expected_row_tags)
        BaseTestCase.assert_json(result.get_column_tags(), [{}, {}, {}, {}])

        # Test with opposite tag option = 'keep first'
        result = TableConcatHelper.concat_table_rows(table_1, table_2, column_tags_option='keep first')
        expected_column_tags = [{'id': 'F1'}, {'id': 'F2'}, {}, {}]
        BaseTestCase.assert_json(result.get_column_tags(), expected_column_tags)

        # Test with opposite tag option = 'merge from first'
        result = TableConcatHelper.concat_table_rows(table_1, table_2, column_tags_option='merge from first')
        expected_column_tags = [{'id': 'F1', 'other': 'top'}, {'id': 'F2'}, {'id': 'F3'}, {'id': 'F4'}]
        BaseTestCase.assert_json(result.get_column_tags(), expected_column_tags)

    def test_table_column_concat_helper(self):
        df_1: DataFrame = DataFrame({'1': [1, 2], '2': ['A2', 'B2']}, index=['A', 'B'])
        table_1 = Table(df_1)

        df_2: DataFrame = DataFrame({'3': ['A3', 'C3'], '4': ['A4', 'C4']}, index=['A', 'C'])
        table_2 = Table(df_2)

        result: Table = TableConcatHelper.concat_table_columns(
            table_1, table_2, row_tags_option='ignore', fill_nan=NaN)

        expected_df = DataFrame(
            {'1': [1, 2, NaN],
             '2': ['A2', 'B2', NaN],
             '3': ['A3', NaN, 'C3'],
             '4': ['A4', NaN, 'C4']},
            index=['A', 'B', 'C'])

        self.assertTrue(DataFrame.equals(result.get_data(), expected_df))
