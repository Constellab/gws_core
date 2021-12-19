
from gws_core import BaseTestCase, TableStackedBarPlotView, ViewTester
from gws_core.extra import DataProvider


class TestTableStackedBarPlotView(BaseTestCase):

    def test_stacked_barplot_2d_view(self,):
        table = DataProvider.get_iris_table()

        tester = ViewTester(
            view=TableStackedBarPlotView(table)
        )
        dic = tester.to_dict(dict(
            column_names=["sepal.length", "petal.length", "petal.width"]
        ))
        self.assertEqual(dic["type"], "stacked-bar-plot-view")
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], list(range(0, table.get_data().shape[0])))
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], list(range(0, table.get_data().shape[0])))
        self.assertEqual(dic["data"]["series"][2]["data"]["x"], list(range(0, table.get_data().shape[0])))
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][2]["data"]["y"], table.get_data()["petal.width"].values.tolist())
