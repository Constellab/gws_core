# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BaseTestCase, ViewTester, ViewType
from gws_core.extra import DataProvider, TableLinePlot2DView
from gws_core.impl.table.view.base_table_view import Serie2d


class TestTableLinePlot2DView(BaseTestCase):

    def test_lineplot_2d_view(self,):
        table = DataProvider.get_iris_table()
        tester = ViewTester(
            view=TableLinePlot2DView(table)
        )

        # 2 series :
        # first : x = sepal.length, y = sepal.width
        # second : x = petal length, y = petal.width
        series: List[Serie2d] = [{"name": "first", "x": {"type": "columns", "selection": ["sepal.length"]},
                                  "y": {"type": "columns", "selection": ["petal.length"]}},
                                 {"name": "second", "x": {"type": "columns", "selection": ["petal.length"]},
                                  "y": {"type": "columns", "selection": ["petal.width"]}}]

        dic = tester.to_dict({"series": series})

        self.assertEqual(dic["type"], ViewType.LINE_PLOT_2D.value)
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["petal.width"].values.tolist())
