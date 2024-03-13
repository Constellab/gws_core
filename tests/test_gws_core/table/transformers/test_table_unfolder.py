

from unittest import TestCase

from numpy import NaN
from pandas import DataFrame

from gws_core import Table, TableUnfolderHelper
from gws_core.test.base_test_case import BaseTestCase


# test_table_unfolder
class TestTableUnfolder(TestCase):

    def test_row_unfolding(self):
        initial_df = DataFrame({'A': range(1, 5), 'B': [10, 8, 6, 4]})

        table = Table(data=initial_df)
        table.set_all_row_tags([{'gender': 'M', 'age': '10'},
                                {'gender': 'F', 'age': '10'},
                                {'gender': 'F', 'age': '10'},
                                {'gender': 'M', 'age': '20'}])
        table.set_all_column_tags([{'test': 'ok'}, {'test': 'nok'}])

        result = TableUnfolderHelper.unfold_rows_by_tags(table, ['gender'], 'column_name')

        # check the unfolding
        expected_result = Table(
            DataFrame({'A_M': [1, 4],
                       'B_M': [10, 4],
                       'A_F': [2, 3],
                       'B_F': [8, 6]}))
        self.assertTrue(result.get_data().equals(expected_result.get_data()))

        # check that the tag used to unfold where set and the column name set as tag and
        # initial column tag are kept
        BaseTestCase.assert_json(
            result.get_column_tags(),
            [{'gender': 'M', 'column_name': 'A', 'test': 'ok'},
             {'gender': 'M', 'column_name': 'B', 'test': 'nok'},
             {'gender': 'F', 'column_name': 'A', 'test': 'ok'},
             {'gender': 'F', 'column_name': 'B', 'test': 'nok'}])

        # test unfolding with multiple tags
        result = TableUnfolderHelper.unfold_rows_by_tags(table, ['gender', 'age'], 'column_name')
        expected_result = Table(
            DataFrame(
                {'A_M_10': [1, NaN],
                 'B_M_10': [10, NaN],
                 'A_M_20': [4, NaN],
                 'B_M_20': [4, NaN],
                 'A_F_10': [2.0, 3.0],
                 'B_F_10': [8.0, 6.0]}))

        self.assertTrue(result.get_data().equals(expected_result.get_data()))

    def test_column_unfolding(self):
        initial_df = DataFrame({'A': [1, 2], 'B': [10, 8], 'C': [3, 4], 'D': [6, 4]})
        initial_df.index = ['a', 'b']

        table = Table(data=initial_df)
        table.set_all_column_tags([{'gender': 'M', 'age': '10'},
                                   {'gender': 'F', 'age': '10'},
                                   {'gender': 'F', 'age': '10'},
                                   {'gender': 'M', 'age': '20'}])
        table.set_all_row_tags([{'test': 'ok'}, {'test': 'nok'}])

        result = TableUnfolderHelper.unfold_columns_by_tags(table, ['gender'], 'row_name')

        # check the unfolding
        expected_result = Table(DataFrame({0: [1, 2, 10, 8], 1: [6, 4, 3, 4]}, index=['a_M', 'b_M', 'a_F', 'b_F']))
        self.assertTrue(result.get_data().equals(expected_result.get_data()))
