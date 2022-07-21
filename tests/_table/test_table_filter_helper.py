# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BaseTestCase, DataframeFilterHelper
from gws_core.impl.table.helper.dataframe_data_filter_helper import \
    DataframeDataFilterHelper
from pandas import DataFrame


class TestTableFilterHelper(BaseTestCase):
    async def test_filter_by_axis_name(self):

        initial_df = DataFrame(
            {'Age': [1, 2, 3, 4],
             'Sex': [8, 6, 4, 2],
             'City': [8, 6, 4, 2],
             'Weight': [8, 6, 4, 2]},
            index=['Luc', 'Lea', 'Mickeal', 'Fred'])

        # filter by row name
        result: DataFrame = DataframeFilterHelper.filter_by_axis_names(
            data=initial_df, axis="row", filters=[{"name": "L.*", "is_regex": True}]
        )
        self.assertEqual(result.index.tolist(), ["Luc", "Lea"])
        self.assertEqual(result.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        # filter by column name
        result = DataframeFilterHelper.filter_by_axis_names(
            data=initial_df, axis="column", filters=[{"name": "Cit.*", "is_regex": True}]
        )
        self.assertEqual(result.index.tolist(), ["Luc", "Lea", "Mickeal", "Fred"])
        self.assertEqual(result.columns.tolist(), ["City"])

    async def test_table_filter_aggregate(self):

        initial_df = DataFrame({'A': [1, 2, 3, 4], 'B': [8, 6, 4, 2]})

        # filter columns where sum > 10 (only B)
        result = DataframeDataFilterHelper.filter_columns_by_aggregated_values(
            data=initial_df, func="sum", comp=">", value=10
        )

        expected_result = DataFrame({'B': [8, 6, 4, 2]})
        self.assertTrue(result.equals(expected_result))

        # filter columns where sum > 0 (all columns)
        result = DataframeDataFilterHelper.filter_columns_by_aggregated_values(
            data=initial_df, func="sum", comp=">", value=0
        )

        self.assertTrue(result.equals(initial_df))

        # Filter row where sum >= 8 (first and second rows)
        result = DataframeDataFilterHelper.filter_rows_by_aggregated_values(
            data=initial_df, func="sum", comp=">=", value=8
        )

        expected_result = DataFrame({'A': [1, 2], 'B': [8, 6]}, index=[0, 1])
        self.assertTrue(result.equals(expected_result))

    async def test_table_filter_numeric_data(self):

        initial_df = DataFrame({'A': [1, 2, 3, 4], 'B': [8, 6, 4, 2]})

        # filter rows where A column value >= 3
        result = DataframeDataFilterHelper.filter_rows_numeric(
            data=initial_df, column_name_regex="A", comp=">=", value=3
        )
        expected_result = DataFrame({'A': [3, 4], 'B': [4, 2]}, index=[2, 3])
        self.assertTrue(result.equals(expected_result))

        # filter rows where A and B columns are >= 3
        result = DataframeDataFilterHelper.filter_rows_numeric(
            data=initial_df, column_name_regex="*", comp=">=", value=3)
        expected_result = DataFrame({'A': [3], 'B': [4]}, index=[2])
        self.assertTrue(result.equals(expected_result))

        # filter columns where first row value is >= 3
        result = DataframeDataFilterHelper.filter_columns_numeric(
            data=initial_df, row_name_regex="0", comp=">=", value=3
        )
        expected_result = DataFrame({'B': [8, 6, 4, 2]})
        self.assertTrue(result.equals(expected_result))

    async def test_table_filter_text_data(self):

        initial_df = DataFrame({'A': ['a', 'b', 'c', 'd'], 'B': ['hello', 'nice', 'tacos', 'house']})

        # filter rows where A column value == b
        result = DataframeDataFilterHelper.filter_rows_text(
            data=initial_df, column_name_regex="A", comp="=", value="b"
        )
        expected_result = DataFrame({'A': ['b'], 'B': ['nice']}, index=[1])
        self.assertTrue(result.equals(expected_result))

        # filter rows where B columns value contains e
        result = DataframeDataFilterHelper.filter_rows_text(
            data=initial_df, column_name_regex="B", comp="contains", value="e"
        )
        expected_result = DataFrame({'A': ['a', 'b', 'd'], 'B': ['hello', 'nice', 'house']},
                                    index=[0, 1, 3])
        self.assertTrue(result.equals(expected_result))

        # filter columns where first row value is == hello
        result = DataframeDataFilterHelper.filter_columns_text(
            data=initial_df, row_name_regex="0", comp="=", value="hello"
        )
        expected_result = DataFrame({'B': ['hello', 'nice', 'tacos', 'house']})
        self.assertTrue(result.equals(expected_result))

    async def test_table_filter_out_helper(self):

        initial_df = DataFrame({'A': range(1, 4), 'B': [10, 8, 6], 'AA': range(5, 8)})
        initial_df.index = ['A', 'B', 'AA']

        # Column remove
        # Remove A column
        sub_df: DataFrame = DataframeFilterHelper.filter_out_by_axis_names(
            data=initial_df, axis="column", filters=[{"name": "A", "is_regex": False}]
        )
        self.assertEqual(sub_df.columns.tolist(), ['B', 'AA'])

        # Remove A and AA columns with regex
        sub_df = DataframeFilterHelper.filter_out_by_axis_names(
            data=initial_df, axis="column", filters=[{"name": "A|AA", "is_regex": True}]
        )
        self.assertEqual(sub_df.columns.tolist(), ['B'])

        # Row remove
        # Remove A row
        sub_df = DataframeFilterHelper.filter_out_by_axis_names(
            data=initial_df, axis="row", filters=[{"name": "A", "is_regex": False}]
        )
        self.assertEqual(sub_df.index.tolist(), ['B', 'AA'])

        # Remove A and AA rows with regex
        sub_df = DataframeFilterHelper.filter_out_by_axis_names(
            data=initial_df, axis="row", filters=[{"name": "A|AA", "is_regex": True}]
        )
        self.assertEqual(sub_df.index.tolist(), ['B'])
