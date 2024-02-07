# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from gws_core import ViewTester, ViewType
from gws_core.extra import DataProvider, TableLinePlot3DView


# test_lineplot_3d_view
class TestTableLinePlot3DView(TestCase):

    def test_lineplot_2d_view(self,):
        table = DataProvider.get_iris_table()

        tester = ViewTester(
            view=TableLinePlot3DView(table)
        )
        dic = tester.to_dict(dict(
            series=[
                {
                    "x_data_column": "sepal_length",
                    "y_data_column": "sepal_width",
                    "z_data_column": "petal_length"
                },
                {
                    "x_data_column": "sepal_length",
                    "y_data_column": "sepal_width",
                    "z_data_column": "petal_width"
                }
            ]
        ))

        self.assertEqual(dic["type"], ViewType.LINE_PLOT_3D.value)
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], table.get_data()["sepal_length"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["sepal_width"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["z"], table.get_data()["petal_length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], table.get_data()["sepal_length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["sepal_width"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["z"], table.get_data()["petal_width"].values.tolist())
