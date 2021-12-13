import os

from gws_core import (BaseTestCase, ConfigParams, File, Settings, Table,
                      TableStackedBarPlotView, ViewTester)
from gws_core.config.config_types import ConfigParams
from gws_core.impl.file.file import File


class TestTableStackedBarPlotView(BaseTestCase):

    def test_stacked_barplot_2d_view(self,):
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
            view=TableStackedBarPlotView(table)
        )
        dic = tester.to_dict(dict(
            column_names=["sepal.length", "petal.length", "petal.width"]
        ))
        self.assertEqual(dic["type"], "stacked-bar-plot-view")
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], list(range(0, table.get_data().shape[0])))
        self.assertEqual(dic["data"]["series"][1]["data"]["x"], list(range(0, table.get_data().shape[0])))
        self.assertEqual(dic["data"]["series"][2]["data"]["x"], list(range(0, table.get_data().shape[0])))
        self.assertEqual(dic["data"]["series"][0]["data"]["y"], table.get_data()["sepal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][1]["data"]["y"], table.get_data()["petal.length"].values.tolist())
        self.assertEqual(dic["data"]["series"][2]["data"]["y"], table.get_data()["petal.width"].values.tolist())
