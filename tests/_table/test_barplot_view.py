import os

from gws_core import (BarPlotView, BaseTestCase, ConfigParams, File, Settings,
                      Table, ViewTester)
from gws_core.config.config_types import ConfigParams
from gws_core.impl.file.file import File


class TestBarPlotView(BaseTestCase):

    def test_barplot_2d_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(
            File(path=file_path),
            ConfigParams({
                "delimiter": ",",
                "header": 0
            })
        )
        tester = ViewTester(
            view=BarPlotView(table)
        )
        dic = tester.to_dict(dict(
            x_column_name="sepal.length",
            y_column_names=["petal.length", "petal.width"]
        ))
        self.assertEqual(dic["type"], "bar-plot-view")
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["petal.width"].values.tolist())
