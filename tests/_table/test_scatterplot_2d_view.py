import os

from gws_core import BaseTestCase, ScatterPlot2DView, Settings, Table, ViewTester, ConfigParams, File


class TestScatterPlot2DView(BaseTestCase):

    def test_scatterplot_2d_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(
            File(path=file_path),
            ConfigParams({
                "delimiter":",",
                "header":0
            })
        )
        tester = ViewTester(
            view = ScatterPlot2DView(data=table)
        )
        dic = tester.to_dict(dict(
            x_column_name="sepal.length",
            y_column_names=["petal.length", "petal.width"]
        ))
        self.assertEqual(dic["type"], "scatter-plot-2d-view")
        self.assertEqual(dic["data"][0]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"][0]["data"]["y"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"][1]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"][1]["data"]["y"], table.get_data()["petal.width"].values.tolist())
