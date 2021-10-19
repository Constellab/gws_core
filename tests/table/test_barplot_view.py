import os

from gws_core import BarPlotView, BaseTestCase, Settings, Table


class TestBarPlotView(BaseTestCase):

    def test_barplot_2d_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(file_path, delimiter=",", head=0)
        vw = BarPlotView(data=table)

        dic = vw.to_dict(x_column_name="sepal.length",
                         y_column_names=["petal.length", "petal.width"],)

        self.assertEqual(dic["type"], "bar-plot-view")

        self.assertEqual(dic["series"][0]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["series"][0]["data"]["y"], table.get_data()["petal.length"].values.tolist())

        self.assertEqual(dic["series"][1]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["series"][1]["data"]["y"], table.get_data()["petal.width"].values.tolist())
