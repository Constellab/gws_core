from unittest import TestCase

from gws_core import Table, TableScalerHelper
from gws_core.impl.table.helper.dataframe_scaler_helper import DataframeScalerHelper
from pandas import DataFrame


# test_table_scaler
class TestTableScaler(TestCase):
    def test_df_scale(self):
        # Test log 2
        df = DataFrame({"A": [1, 2], "B": [32, 16]})
        expected_df = DataFrame({"A": [0.0, 1.0], "B": [5.0, 4.0]})

        result = DataframeScalerHelper.scale(df, "log2")
        self.assertTrue(result.equals(expected_df))

        # Test log 10
        df = DataFrame({"A": [1, 10], "B": [1000, 100]})
        expected_df = DataFrame({"A": [0.0, 1.0], "B": [3.0, 2.0]})

        result = DataframeScalerHelper.scale(df, "log10")
        self.assertTrue(result.equals(expected_df))

        # Test log
        df = DataFrame({"A": [1, 10], "B": [1000, 100]})
        expected_df = DataFrame(
            {"A": [0.0, 2.302585092994046], "B": [6.907755278982137, 4.605170185988092]}
        )

        result = DataframeScalerHelper.scale(df, "log")
        self.assertTrue(result.equals(expected_df))

    def test_df_scale_by_columns(self):
        # Test unit
        df = DataFrame({"A": [1, 4], "B": [3, 9]})
        expected_df = DataFrame({"A": [0.20, 0.80], "B": [0.25, 0.75]})

        result = DataframeScalerHelper.scale_by_columns(df, func="unit")
        self.assertTrue(result.equals(expected_df))

        # Test percent
        df = DataFrame({"A": [1, 4], "B": [3, 9]})
        expected_df = DataFrame({"A": [20.0, 80.0], "B": [25.0, 75.0]})

        result = DataframeScalerHelper.scale_by_columns(df, func="percent")
        self.assertTrue(result.equals(expected_df))

        # Test standard
        df = DataFrame({"A": [1, 4, 3], "B": [3, 9, 5]})

        result = DataframeScalerHelper.scale_by_columns(df, func="standard")
        # mean of the result should be 0
        mean_result = result.mean().round(3)
        self.assertEqual(mean_result.iloc[0], 0.0)
        self.assertEqual(mean_result.iloc[1], -0.0)

        # standard of the result should be 1
        std_result = result.std().round(3)
        self.assertEqual(std_result.iloc[0], 1.0)
        self.assertEqual(std_result.iloc[1], 1.0)

    def test_df_scale_by_rows(self):
        # Test unit
        df = DataFrame({"A": [1, 3], "B": [4, 9]})
        expected_df = DataFrame({"A": [0.20, 0.25], "B": [0.80, 0.75]})

        result = DataframeScalerHelper.scale_by_rows(df, func="unit")
        self.assertTrue(result.equals(expected_df))

        # Test percent
        df = DataFrame({"A": [1, 3], "B": [4, 9]})
        expected_df = DataFrame({"A": [20.0, 25.0], "B": [80.0, 75.0]})

        result = DataframeScalerHelper.scale_by_rows(df, func="percent")
        self.assertTrue(result.equals(expected_df))

        # Test standard
        df = DataFrame({"A": [1, 4], "B": [3, 9], "C": [6, 7]})

        result = DataframeScalerHelper.scale_by_rows(df, func="standard")
        # mean of the result should be 0
        mean_result = result.mean(axis=1).round(3)
        self.assertEqual(mean_result[0], -0.0)
        self.assertEqual(mean_result[1], -0.0)

        # standard of the result should be 1
        std_result = result.std(axis=1).round(3)
        self.assertEqual(std_result[0], 1.0)
        self.assertEqual(std_result[1], 1.0)

    def test_table_scale(self):
        df = DataFrame({"A": [1, 2], "B": [32, 16]})

        row_tags = [{"ROW": 1}, {"ROW": 2}]
        column_tags = [{"COLUMN": 1}, {"COLUMN": 2}]
        table = Table(df, row_tags=row_tags, column_tags=column_tags)

        result = TableScalerHelper.scale(table, func="log2")

        expected_df = DataFrame({"A": [0.0, 1.0], "B": [5.0, 4.0]})
        expected_table = Table(expected_df, row_tags=row_tags, column_tags=column_tags)

        self.assertTrue(result.equals(expected_table))
