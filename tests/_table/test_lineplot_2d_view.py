
from gws_core import BaseTestCase, TableLinePlot2DView, ViewTester
from gws_core.extra import DataProvider


class TestTableLinePlot2DView(BaseTestCase):

    def test_lineplot_2d_view(self,):
        table = DataProvider.get_iris_table()
        tester = ViewTester(
            view=TableLinePlot2DView(table)
        )
        dic = tester.to_dict(dict(
            series=[
                {
                    "x_data_column": "sepal.length",
                    "y_data_column": "petal.length"
                },
                {
                    "x_data_column": "petal.length",
                    "y_data_column": "petal.width"
                }
            ]
        ))

        self.assertEqual(dic["type"], "line-plot-2d-view")
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["petal.width"].values.tolist())
