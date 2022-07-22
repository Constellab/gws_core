# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import DataframeAggregatorHelper, Table, TaskRunner
from gws_core.impl.table.transformers.table_aggregator import \
    TableColumnAggregator
from gws_core.test.base_test_case import BaseTestCase
from numpy import NaN
from pandas import DataFrame


class TestTableAggregator(BaseTestCase):
    async def test_table_aggregator_helper(self):
        initial_df = DataFrame({'A': range(1, 5), 'B': [10, 8, 6, 4]})

        df = DataframeAggregatorHelper.aggregate(data=initial_df, direction="vertical", func="sum")
        expected_df = DataFrame({'A': [10], 'B': [28]})
        self.assertTrue(df.equals(expected_df))

        # test with string and NaN in the dataframe
        df_with_str = DataFrame({'A': [1, 2, 3, 'OK'], 'B': [10, None, 6, NaN]})

        df = DataframeAggregatorHelper.aggregate(data=df_with_str, direction="vertical", func="sum")
        expected_df = DataFrame({'A': [6.0], 'B': [16.0]})
        self.assertTrue(df.equals(expected_df))

        # Horizontal
        df = DataframeAggregatorHelper.aggregate(data=initial_df, direction="horizontal", func="sum")
        expected_df = DataFrame({0: [11, 10, 9, 8]})
        self.assertTrue(df.equals(expected_df))

    async def test_table_aggregator(self):
        initial_df = DataFrame({'A': [1, 2], 'B': [10, 8]})
        table = Table(data=initial_df)
        column_tags = [{'test': 'ok'}, {'test': 'nok'}]
        table.set_all_columns_tags(column_tags)

        # Vertical
        task_runner = TaskRunner(TableColumnAggregator, {"function": "sum"})
        task_runner.set_input('source', table)
        await task_runner.run()
        result: Table = task_runner.get_output('target')

        expected_df = DataFrame({'A': [3], 'B': [18]})
        self.assertTrue(result.get_data().equals(expected_df))
        self.assert_json(result.get_column_tags(), column_tags)
