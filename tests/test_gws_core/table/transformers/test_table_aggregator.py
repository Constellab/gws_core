from unittest import TestCase

from numpy import NaN
from pandas import NA, DataFrame

from gws_core import DataframeAggregatorHelper, Table, TaskRunner
from gws_core.core.utils.utils import Utils
from gws_core.impl.table.transformers.table_aggregator import TableColumnAggregator


# test_table_aggregator
class TestTableAggregator(TestCase):
    def test_table_aggregator_helper(self):
        initial_df = DataFrame({"A": range(1, 5), "B": [10, 8, 6, 4]})

        dataframe = DataframeAggregatorHelper.aggregate(
            data=initial_df, direction="vertical", func="sum"
        )
        expected_df = DataFrame({"A": [10], "B": [28]})
        self.assertTrue(dataframe.equals(expected_df))

        # test with string and NaN in the dataframe
        df_with_str = DataFrame({"A": [1, 2, 3, "OK"], "B": [10, None, NaN, NA]})

        dataframe = DataframeAggregatorHelper.aggregate(
            data=df_with_str, direction="vertical", func="sum"
        )
        expected_df = DataFrame({"A": [6.0], "B": [10.0]})
        self.assertTrue(dataframe.equals(expected_df))

        # Horizontal
        dataframe = DataframeAggregatorHelper.aggregate(
            data=initial_df, direction="horizontal", func="sum"
        )
        expected_df = DataFrame({0: [11, 10, 9, 8]})
        self.assertTrue(dataframe.equals(expected_df))

    def test_table_aggregator(self):
        initial_df = DataFrame({"A": [1, 2], "B": [10, 8]})
        table = Table(data=initial_df)
        column_tags = [{"test": "ok"}, {"test": "nok"}]
        table.set_all_column_tags(column_tags)

        # Vertical
        task_runner = TaskRunner(TableColumnAggregator, {"function": "sum"})
        task_runner.set_input("source", table)
        task_runner.run()
        result: Table = task_runner.get_output("target")

        expected_result = Table(DataFrame({"A": [3], "B": [18]}))
        self.assertTrue(result.get_data().equals(expected_result.get_data()))
        Utils.assert_json_equals(result.get_column_tags(), column_tags)
