# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List
from unittest import TestCase

from gws_core import ViewTester, ViewType
from gws_core.extra import DataProvider, TableBoxPlotView
from gws_core.impl.table.view.table_selection import Serie1d


# test_boxplot_view
class TestTableBoxPlotView(TestCase):

    def test_boxplot_view(self,):
        table = DataProvider.get_iris_table()
        tester = ViewTester(
            view=TableBoxPlotView(table)
        )

        # 1 series :
        # first : y = petal_length
        series: List[Serie1d] = [{"name": "first", "y": {"type": "columns", "selection": ["petal_length"]}}]
        dic = tester.to_dict({"series": series})
        self.assertEqual(dic["type"], ViewType.BOX_PLOT.value)

        first_data = dic["data"]["series"][0]["data"]
        self.assertEqual(first_data['x'][0], 0)
        self.assertEqual(first_data['min'][0], 1.0)
        self.assertEqual(first_data['q1'][0], 1.6)
        self.assertEqual(first_data['median'][0], 4.35)
        self.assertEqual(first_data['q3'][0], 5.1)
        self.assertEqual(first_data['max'][0], 6.9)
        self.assertEqual(round(first_data['lower_whisker'][0], 2), 1.4)
        self.assertEqual(round(first_data['upper_whisker'][0], 2), 5.8)
