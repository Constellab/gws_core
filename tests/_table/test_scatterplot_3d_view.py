# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from gws_core import BaseTestCase, ViewTester, ViewType
from gws_core.extra import DataProvider, TableScatterPlot3DView


class TestTableScatterPlot2DView(BaseTestCase):

    async def test_scatterplot_2d_view(self,):
        table = DataProvider.get_iris_table()

        tester = ViewTester(
            view=TableScatterPlot3DView(table)
        )
        dic = tester.to_dict(dict(
            series=[
                {
                    "x_data_column": "sepal.length",
                    "y_data_column": "sepal.width",
                    "z_data_column": "petal.length"
                },
                {
                    "x_data_column": "sepal.length",
                    "y_data_column": "sepal.width",
                    "z_data_column": "petal.width"
                }
            ]
        ))
        self.assertEqual(dic["type"], ViewType.SCATTER_PLOT_3D.value)
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["sepal.width"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["z"], table.get_data()["petal.length"].values.tolist())

        self.assertEqual(dic["data"]["series"][1]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["sepal.width"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["z"], table.get_data()["petal.width"].values.tolist())

    async def test_scatterplot_2d_view_without_params(self):
        table = DataProvider.get_iris_table()

        tester = ViewTester(
            view=TableScatterPlot3DView(table)
        )
        dic = tester.to_dict(dict(
            series=[]
        ))
        self.assertEqual(dic["type"], ViewType.SCATTER_PLOT_3D.value)
        x = list(range(0, table.get_data().shape[0]))
        y = x
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], x)
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], y)
        self.assertEqual(dic["data"]["series"][0]["data"]["z"], table.get_data()["sepal.length"].values.tolist())

        self.assertEqual(dic["data"]["series"][1]["data"]["x"], x)
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], y)
        self.assertEqual(dic["data"]["series"][1]["data"]["z"], table.get_data()["sepal.width"].values.tolist())
