

from unittest import TestCase

from gws_core import Table, TableUnfolderHelper
from gws_core.test.base_test_case import BaseTestCase
from numpy import NaN
from pandas import DataFrame


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

    def test_helper_unfold_columns_by_rows(self):
        """Test the TableUnfolderHelper.unfold_columns_by_rows method directly."""
        initial_df = DataFrame({
            'A': [1, 2, 3],
            'B': [10, 20, 30]
        })
        initial_df.index = ['row1', 'row2', 'header_row']

        table = Table(data=initial_df)
        helper = TableUnfolderHelper()

        # Test the helper method directly
        result = helper.unfold_by_rows(table, ['header_row'], 'original_column')

        # Verify the header_row was extracted and used for column tags
        self.assertNotIn('header_row', result.get_data().index)

        # Check that new rows were created based on the values from header_row
        # The values [3, 30] should be used to create column tags and unfold
        self.assertTrue(len(result.get_data().index) > 0)
        self.assertEqual(result.get_data().shape[1], 1)  # Should have 1 column after unfolding

    def test_helper_unfold_rows_by_columns(self):
        """Test the TableUnfolderHelper.unfold_rows_by_columns method directly."""
        initial_df = DataFrame({
            'A': ['header1', 'header2'],
            'B': [10, 20],
            'C': [100, 200]
        })
        initial_df.index = ['row1', 'row2']

        table = Table(data=initial_df)
        helper = TableUnfolderHelper()

        # Test the helper method directly
        result = helper.unfold_by_columns(table, ['A'], 'original_row')

        # Verify column A was extracted and used for row tags
        self.assertNotIn('A', result.get_data().columns)

        # Check that new columns were created based on the values from column A
        # The values ['header1', 'header2'] should be used to create row tags and unfold
        column_names = result.get_data().columns.tolist()
        self.assertTrue(any('header1' in col for col in column_names))
        self.assertTrue(any('header2' in col for col in column_names))

        # Should have 1 row and multiple columns after unfolding
        self.assertEqual(result.get_data().shape[0], 1)
        self.assertTrue(result.get_data().shape[1] > 2)
