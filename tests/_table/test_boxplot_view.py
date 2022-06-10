# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BaseTestCase, ViewTester, ViewType
from gws_core.extra import DataProvider, TableBoxPlotView
from gws_core.impl.table.view.table_selection import Serie2d


class TestTableBoxPlotView(BaseTestCase):

    def test_boxplot_view(self,):
        table = DataProvider.get_iris_table()
        tester = ViewTester(
            view=TableBoxPlotView(table)
        )

        # 1 series :
        # first : y = petal.length
        series: List[Serie2d] = [{"name": "first", "y": {"type": "columns", "selection": ["petal.length"]}}]
        dic = tester.to_dict({"series": series})
        self.assertEqual(dic["type"], ViewType.BOX_PLOT.value)

        first_data = dic["data"]["series"][0]["data"]
        self.assertEqual(first_data['x'][0], 0)
        self.assertEqual(first_data['min'][0], 1.0)
        self.assertEqual(first_data['q1'][0], 1.6)
        self.assertEqual(first_data['median'][0], 4.35)
        self.assertEqual(first_data['q3'][0], 5.1)
        self.assertEqual(first_data['max'][0], 6.9)
        self.assertEqual(round(first_data['lower_whisker'][0], 2), -3.65)
        self.assertEqual(round(first_data['upper_whisker'][0], 2), 10.35)
