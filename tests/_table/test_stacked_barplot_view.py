# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BaseTestCase, ViewTester, ViewType
from gws_core.extra import DataProvider, TableStackedBarPlotView
from gws_core.impl.table.view.base_table_view import Serie1d


class TestTableStackedBarPlotView(BaseTestCase):

    def test_stacked_barplot_2d_view(self,):
        table = DataProvider.get_iris_table()

        tester = ViewTester(
            view=TableStackedBarPlotView(table)
        )

        # 3 series :
        # first : y = sepal.length
        # second :  y = petal.length
        # third :  y = petal.width
        series: List[Serie1d] = [{"name": "first", "y": {"type": "columns", "selection": ["sepal.length"]}},
                                 {"name": "second", "y": {"type": "columns", "selection": ["petal.length"]}},
                                 {"name": "third", "y": {"type": "columns", "selection": ["petal.width"]}}
                                 ]
        dic = tester.to_dict({"series": series})

        x = list(range(0, table.get_data().shape[0]))
        self.assertEqual(dic["type"], ViewType.STACKED_BAR_PLOT.value)
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], x)
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], x)
        self.assertEqual(dic["data"]["series"][2]["data"]["x"], x)
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][2]["data"]["y"], table.get_data()["petal.width"].values.tolist())
