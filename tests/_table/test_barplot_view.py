
from gws_core import BaseTestCase, TableBarPlotView, ViewTester
from gws_core.extra import DataProvider


class TestTableBarPlotView(BaseTestCase):

    def test_barplot_2d_view(self,):
        table = DataProvider.get_iris_table()

        tester = ViewTester(
            view=TableBarPlotView(table)
        )
        dic = tester.to_dict(dict(
            column_names=["sepal.length", "petal.length", "petal.width"]
        ))
        self.assertEqual(dic["type"], "bar-plot-view")
        self.assertEqual(dic["data"]["x_tick_labels"], list(range(0, table.get_data().shape[0])))
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], list(range(0, table.get_data().shape[0])))
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], list(range(0, table.get_data().shape[0])))
        self.assertEqual(dic["data"]["series"][2]["data"]["x"], list(range(0, table.get_data().shape[0])))

        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][2]["data"]["y"], table.get_data()["petal.width"].values.tolist())
