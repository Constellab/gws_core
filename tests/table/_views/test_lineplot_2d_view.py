# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List
from unittest import TestCase

from gws_core import ViewTester, ViewType
from gws_core.extra import DataProvider, TableLinePlot2DView
from gws_core.impl.table.view.table_selection import Serie2d


# test_lineplot_2d_view
class TestTableLinePlot2DView(TestCase):

    def test_lineplot_2d_view(self):
        table = DataProvider.get_iris_table()
        tester = ViewTester(
            view=TableLinePlot2DView(table)
        )

        # 2 series :
        # first : x = sepal_length, y = sepal_width
        # second : x = petal length, y = petal_width
        series: List[Serie2d] = [{"name": "first", "x": {"type": "columns", "selection": ["sepal_length"]},
                                  "y": {"type": "columns", "selection": ["petal_length"]}},
                                 {"name": "second", "x": {"type": "columns", "selection": ["petal_length"]},
                                  "y": {"type": "columns", "selection": ["petal_width"]}}]

        dic = tester.to_dict({"series": series})

        self.assertEqual(dic["type"], ViewType.LINE_PLOT_2D.value)
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], table.get_data()["sepal_length"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["petal_length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], table.get_data()["petal_length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["petal_width"].values.tolist())
