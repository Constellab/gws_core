# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from numpy import NaN
from pandas import NA, DataFrame

from gws_core.impl.table.helper.dataframe_helper import DataframeHelper


# test_dataframe_helper
class TestTableConcat(TestCase):

    def test_detect_csv_delimiter(self):
        csv_str = "1,2,3\n4,5,6"
        self.assertEqual(DataframeHelper.detect_csv_delimiter(csv_str), ",")

    def test_flatten_dataframe_by_column(self):
        df = DataFrame({'F1': [1, 2], 'F2': [7, 1]})
        self.assertEqual(DataframeHelper.flatten_dataframe_by_column(df), [1, 2, 7, 1])

    def test_dataframe_to_float(self):
        df = DataFrame({'F1': ['1', 2], 'F2': ['NA', NaN]})
        self.assertTrue(DataframeHelper.dataframe_to_float(df).equals(DataFrame({'F1': [1.0, 2.0], 'F2': [NaN, NaN]})))

    def test_dataframe_bool(self):
        df = DataFrame({'F1': ['Seoul', 'Paris'], 'F2': ['Madrid', 'Liverpool']})

        # check contains
        result = DataframeHelper.contains(df, 'adri')
        self.assertTrue(result.equals(DataFrame({'F1': [False, False], 'F2': [True, False]})))

        # check not contains
        result = DataframeHelper.contains_not(df, 'adri')
        self.assertTrue(result.equals(DataFrame({'F1': [True, True], 'F2': [False, True]})))

        # check start with
        result = DataframeHelper.starts_with(df, 'Pa')
        self.assertTrue(result.equals(DataFrame({'F1': [False, True], 'F2': [False, False]})))

        # check end with
        result = DataframeHelper.ends_with(df, 'l')
        self.assertTrue(result.equals(DataFrame({'F1': [True, False], 'F2': [False, True]})))

    def test_rename_duplicate_column_names(self):
        df = DataFrame([[1, 2, 3, 4, 5, 6]], columns=['A', 'B', 'A', 'B', 'A', 'A_1'])

        result = DataframeHelper.rename_duplicate_column_names(df)
        expected_result = DataFrame([[1, 2, 3, 4, 5, 6]], columns=['A', 'B', 'A_1', 'B_1', 'A_2', 'A_1_1'])

        self.assertTrue(result.equals(expected_result))

    def test_rename_duplicate_row_names(self):
        df = DataFrame([1, 2, 3, 4, 5, 6], index=['A', 'B', 'A', 'B', 'A', 'A_1'])

        result = DataframeHelper.rename_duplicate_row_names(df)
        expected_result = DataFrame([1, 2, 3, 4, 5, 6], index=['A', 'B', 'A_1', 'B_1', 'A_2', 'A_1_1'])

        self.assertTrue(result.equals(expected_result))

    def test_nanify_none_numeric(self):
        df = DataFrame({'F1': ['1', 2, None, NaN, NA]})

        result = DataframeHelper.nanify_none_number(df)
        expected_result = DataFrame({'F1': [NaN, 2.0, NaN, NaN, NaN]})

        self.assertTrue(result.equals(expected_result))
