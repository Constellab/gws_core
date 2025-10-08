

from typing import List
from unittest import TestCase

from gws_core import ViewTester, ViewType
from gws_core.extra import TableBoxPlotView
from gws_core.impl.table.view.table_selection import Serie1d
from gws_core.test.data_provider import DataProvider


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
        view_dto = tester.to_dto({"series": series})
        self.assertEqual(view_dto.type, ViewType.BOX_PLOT)

        first_data = view_dto.data["series"][0]["data"]
        self.assertEqual(first_data['x'][0], 0)
        self.assertEqual(first_data['min'][0], 1.0)
        self.assertEqual(first_data['q1'][0], 1.6)
        self.assertEqual(first_data['median'][0], 4.35)
        self.assertEqual(first_data['q3'][0], 5.1)
        self.assertEqual(first_data['max'][0], 6.9)
        self.assertEqual(round(first_data['lower_whisker'][0], 2), 1.4)
        self.assertEqual(round(first_data['upper_whisker'][0], 2), 5.8)
