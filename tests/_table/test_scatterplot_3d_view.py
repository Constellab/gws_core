
from gws_core import BaseTestCase, TableScatterPlot3DView, ViewTester
from gws_core.extra import DataProvider


class TestTableScatterPlot2DView(BaseTestCase):

    async def test_scatterplot_2d_view(self,):
        table = DataProvider.get_iris_table()

        tester = ViewTester(
            view=TableScatterPlot3DView(table)
        )
        dic = tester.to_dict(dict(
            x_column_name="sepal.length",
            y_column_name="sepal.width",
            z_column_names=["petal.length", "petal.width"]
        ))
        self.assertEqual(dic["type"], "scatter-plot-3d-view")
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["sepal.width"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["z"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["sepal.width"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["z"], table.get_data()["petal.width"].values.tolist())
