
from gws_core import BaseTestCase, TableScatterPlot2DView, ViewTester
from gws_core.extra import DataProvider


class TestTableScatterPlot2DView(BaseTestCase):

    def test_scatterplot_2d_view(self,):
        table = DataProvider.get_iris_table()

        tester = ViewTester(
            view=TableScatterPlot2DView(data=table)
        )
        dic = tester.to_dict(dict(
            x_column_name="sepal.length",
            y_column_names=["petal.length", "petal.width"]
        ))
        self.assertEqual(dic["type"], "scatter-plot-2d-view")
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["petal.length"].values.tolist())

        self.assertEqual(dic["data"]["series"][1]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["petal.width"].values.tolist())
