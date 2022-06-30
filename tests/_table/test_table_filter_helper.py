# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, DataframeFilterHelper, Settings, Table,
                      TableImporter)
from gws_core.data_provider.data_provider import DataProvider
from pandas import DataFrame

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTableFilterHelper(BaseTestCase):
    async def test_table_filter_helper(self):
        file = DataProvider.get_test_data_file("multi_index_data.csv")
        table: Table = TableImporter.call(file, {"header": 0, "index_column": 0})

        # filter by row name
        df = DataframeFilterHelper.filter_by_axis_names(
            data=table.get_data(), axis="row", filters=[{"name": "L.*a$", "is_regex": True}]
        )
        self.assertEqual(df.index.tolist(), ["Lea", "Laura"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        # filter by column name
        df = DataframeFilterHelper.filter_by_axis_names(
            data=table.get_data(), axis="column", filters=[{"name": "Cit.*", "is_regex": True}]
        )
        self.assertEqual(df.index.tolist(), ["Luc", "Lea", "Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["City"])

        # filter by aggreated column
        df = DataframeFilterHelper.filter_by_aggregated_values(
            data=table.get_data(), direction="vertical", func="sum", comp=">=", value=100
        )
        self.assertEqual(df.index.tolist(), ["Luc", "Lea", "Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age", "Weight"])

        # filter by aggreated column
        df = DataframeFilterHelper.filter_by_aggregated_values(
            data=table.get_data(), direction="vertical", func="sum", comp=">=", value=150
        )
        self.assertEqual(df.index.tolist(), ["Luc", "Lea", "Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Weight"])

        # filter by aggreated column
        df = DataframeFilterHelper.filter_by_aggregated_values(
            data=table.get_data(), direction="vertical", func="sum", comp="<", value=150
        )
        self.assertEqual(df.index.tolist(), ["Luc", "Lea", "Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age"])

        # filter by aggreated column
        df = DataframeFilterHelper.filter_by_aggregated_values(
            data=table.get_data(), direction="vertical", func="median", comp=">=", value=150
        )
        self.assertTrue(df.empty)

        # filter by aggreated row
        df = DataframeFilterHelper.filter_by_aggregated_values(
            data=table.get_data(), direction="horizontal", func="var", comp=">=", value=50
        )
        self.assertEqual(df.index.tolist(), ["Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        # filter numeric data
        df = DataframeFilterHelper.filter_numeric_data(
            data=table.get_data(), column_name="Age", comp=">=", value=30
        )
        self.assertEqual(df.index.tolist(), ["Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        # filter numeric data
        df = DataframeFilterHelper.filter_numeric_data(
            data=table.get_data(), column_name="Age|Weight", comp=">=", value=30
        )
        self.assertEqual(df.index.tolist(), ["Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        df = DataframeFilterHelper.filter_numeric_data(
            data=table.get_data(), column_name="Age|Sex", comp=">=", value=30
        )
        self.assertTrue(df.empty)

        df = DataframeFilterHelper.filter_text_data(
            data=table.get_data(), column_name="Sex", comp="=", value="M"
        )
        self.assertEqual(df.index.tolist(), ["Luc", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        df = DataframeFilterHelper.filter_text_data(
            data=table.get_data(), column_name="Sex", comp="!=", value="M"
        )
        self.assertEqual(df.index.tolist(), ["Lea", "Laura"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

    async def test_table_filter_out_helper(self):

        initial_df = DataFrame({'A': range(1, 4), 'B': [10, 8, 6], 'AA': range(5, 8)})
        initial_df.index = ['A', 'B', 'AA']

        # Column remove
        # Remove A column
        sub_df = DataframeFilterHelper.filter_out_by_axis_names(
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
