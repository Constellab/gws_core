

from typing import List
from unittest import TestCase

from gws_core import ViewTester, ViewType
from gws_core.extra import DataProvider, TableStackedBarPlotView
from gws_core.impl.table.view.table_selection import Serie1d


# test_stacked_barplot_view
class TestTableStackedBarPlotView(TestCase):

    def test_stacked_barplot_2d_view(self,):
        table = DataProvider.get_iris_table()

        tester = ViewTester(
            view=TableStackedBarPlotView(table)
        )

        # 3 series :
        # first : y = sepal_length
        # second :  y = petal_length
        # third :  y = petal_width
        series: List[Serie1d] = [{"name": "first", "y": {"type": "columns", "selection": ["sepal_length"]}},
                                 {"name": "second", "y": {"type": "columns", "selection": ["petal_length"]}},
                                 {"name": "third", "y": {"type": "columns", "selection": ["petal_width"]}}
                                 ]
        view_dto = tester.to_dto({"series": series})

        x = list(range(0, table.get_data().shape[0]))
        self.assertEqual(view_dto.type, ViewType.STACKED_BAR_PLOT)
        self.assertEqual(view_dto.data["series"][0]["data"]["x"], x)
        self.assertEqual(view_dto.data["series"][1]["data"]["x"], x)
        self.assertEqual(view_dto.data["series"][2]["data"]["x"], x)
        self.assertEqual(view_dto.data["series"][0]["data"]["y"], table.get_data()["sepal_length"].values.tolist())
        self.assertEqual(view_dto.data["series"][1]["data"]["y"], table.get_data()["petal_length"].values.tolist())
        self.assertEqual(view_dto.data["series"][2]["data"]["y"], table.get_data()["petal_width"].values.tolist())
