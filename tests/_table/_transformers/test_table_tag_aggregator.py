# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from unittest import IsolatedAsyncioTestCase

from gws_core import Table, TableTagAggregatorHelper
from gws_core.test.base_test_case import BaseTestCase
from pandas import DataFrame


# test_table_tag_aggregator
class TestTableTagAggregator(IsolatedAsyncioTestCase):
    async def test_table_tag_aggregator_helper(self):

        initial_df = DataFrame({'F1': [1, 2, 3, 4], 'F2': [7, 1, 10, 8], 'F3': [2, 1, 4, 2]})
        row_tags = [{'gender': 'M', 'town': 'Lyon'},
                    {'gender': 'F', 'town': 'Lyon'},
                    {'gender': 'M', 'town': 'Paris'},
                    {'gender': 'F', 'town': 'Lyon'}]
        column_tags = [{'group': 'A'}, {'group': 'A'}, {'group': 'B'}]

        table = Table(initial_df, row_tags=row_tags, column_tags=column_tags)

        # Sort
        sorted_table = TableTagAggregatorHelper.aggregate_by_row_tags(table, keys=['gender'], func="sort")
        self.assertEqual(sorted_table.row_names, [1, 3, 0, 2])

        # Check that the tags where not affected
        BaseTestCase.assert_json(table.get_column_tags(), column_tags)
        BaseTestCase.assert_json(table.get_row_tags(), row_tags)

        sorted_table = TableTagAggregatorHelper.aggregate_by_row_tags(
            table, keys=['town', 'gender'], func="sort")
        self.assertEqual(sorted_table.row_names, [1, 3, 0, 2])

        # Mean on row
        grouped_table = TableTagAggregatorHelper.aggregate_by_row_tags(table, keys=['gender'], func="mean")

        result_df = DataFrame({'F1': [3.0, 2.0], 'F2': [4.5, 8.5], 'F3': [1.5, 3.0]}, index=["F", "M"])
        self.assertTrue(result_df.equals(grouped_table.get_data()))
        # check that the column tags are not affected
        BaseTestCase.assert_json(grouped_table.get_column_tags(), column_tags)

        # check that only the selected row tag are present
        BaseTestCase.assert_json(grouped_table.get_row_tags(), [{'gender': 'F'}, {'gender': 'M'}])

        # Sum on column
        grouped_table = TableTagAggregatorHelper.aggregate_by_column_tags(table, keys=['group'], func="sum")

        result_df = DataFrame({'A': [8, 3, 13, 12], 'B': [2, 1, 4, 2]}, index=[0, 1, 2, 3])
        self.assertTrue(result_df.equals(grouped_table.get_data()))
        BaseTestCase.assert_json(grouped_table.get_column_tags(), [{'group': 'A'}, {'group': 'B'}])
        BaseTestCase.assert_json(grouped_table.get_row_tags(), row_tags)
