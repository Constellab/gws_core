
from gws_core import BaseTestCase, TableLinePlot3DView, ViewTester
from tests.gws_core_test_helper import GwsCoreTestHelper


class TestTableLinePlot3DView(BaseTestCase):

    def test_lineplot_2d_view(self,):
        table = await GwsCoreTestHelper.get_iris_table()

        tester = ViewTester(
            view=TableLinePlot3DView(table)
        )
        dic = tester.to_dict(dict(
            x_column_name="sepal.length",
            y_column_name="sepal.width",
            z_column_names=["petal.length", "petal.width"]
        ))
        self.assertEqual(dic["type"], "line-plot-3d-view")
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["sepal.width"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["z"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["sepal.width"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["z"], table.get_data()["petal.width"].values.tolist())
