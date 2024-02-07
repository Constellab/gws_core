# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from gws_core import ViewTester, ViewType
from gws_core.extra import DataProvider, TableHeatmapView
from gws_core.impl.table.view.table_selection import Serie1d


# test_heatmap_view
class TestTableHeatmapView(TestCase):

    def test_heatmap_view(self,):
        table = DataProvider.get_iris_table()
        tester = ViewTester(
            view=TableHeatmapView(table)
        )

        # 1 series with all columns
        serie: Serie1d = {"name": "first", "y": {"type": "columns", "selection": [
            "sepal_length",  "sepal_width", "petal_length", "petal_width"]}}

        view_dict = tester.to_dict({"serie": serie})
        self.assertEqual(view_dict["type"], ViewType.HEATMAP.value)
        self.assertEqual(
            view_dict["data"]["table"],
            table.to_dataframe().iloc[0:, 0:4].to_dict('split')["data"]
        )
