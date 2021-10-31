import os

import numpy
from gws_core import BaseTestCase, BoxPlotView, Settings, Table, ViewTester, ConfigParams, File


class TestBoxPlotView(BaseTestCase):

    def test_boxplot_view(self,):
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
            view = BoxPlotView(table)
        )
        dic = tester.to_dict(dict(
            column_names=["petal.length", "petal.width"]
        ))
        self.assertEqual(dic["type"], "box-plot-view")

        self.assertEqual(dic["data"][0]["data"]["min"], 1.0)
        self.assertEqual(dic["data"][0]["data"]["q1"], 1.6)
        self.assertEqual(dic["data"][0]["data"]["median"], 4.35)
        self.assertEqual(dic["data"][0]["data"]["q3"], 5.1)
        self.assertEqual(dic["data"][0]["data"]["max"], 6.9)

        self.assertEqual(dic["data"][1]["data"]["min"], 0.1)
        self.assertEqual(dic["data"][1]["data"]["q1"], 0.3)
        self.assertEqual(dic["data"][1]["data"]["median"], 1.3)
        self.assertEqual(dic["data"][1]["data"]["q3"], 1.8)
        self.assertEqual(dic["data"][1]["data"]["max"], 2.5)

