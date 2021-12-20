# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BaseTestCase, Table, TableAggregatorHelper, TableImporter
from gws_core.data_provider.data_provider import DataProvider
from pandas import Series


class TestTableAggregatorHelper(BaseTestCase):
    async def test_table_aggregator_helper(self):
        file = DataProvider.get_test_data_file("multi_index_data.csv")
        table: Table = TableImporter.call(file, {"header": 0, "index_columns": ["Name"]})

        df = TableAggregatorHelper.aggregate(data=table.get_data(), direction="vertical", func="sum")
        exptect_df = Series(data=[110, 170], index=["Age", "Weight"])
        self.assertTrue(df.equals(exptect_df))

        df = TableAggregatorHelper.aggregate(data=table.get_data(), direction="vertical", func="mean")
        exptect_df = Series(data=[27.5, 42.5], index=["Age", "Weight"])
        self.assertTrue(df.equals(exptect_df))

        df = TableAggregatorHelper.aggregate(data=table.get_data(), direction="horizontal", func="median")
        exptect_df = Series(data=[12.5, 16.0, 59.0, 52.5], index=["Luc", "Lea", "Laura", "Leon"])
        self.assertTrue(df.equals(exptect_df))
