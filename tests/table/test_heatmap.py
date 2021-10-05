import os

import numpy
from gws_core import BaseTestCase, HeatmapView, Settings, Table


class TestHeatmapView(BaseTestCase):

    def test_heatmap_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(file_path, delimiter=",", head=0)
        vw = HeatmapView(table, ["petal.length", "petal.width"])

        dic = vw.to_dict()

        self.assertEqual(dic["type"], "heatmap")

        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][0]["data"],
            table.get_data()[["petal.length", "petal.width"]],
            rtol=1e-03, atol=1e-03, equal_nan=False
        )))

        vw = HeatmapView(table, ["petal.length", "petal.width"], scale="log10")
        dic = vw.to_dict()
        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][0]["data"],
            numpy.log10(table.get_data()[["petal.length", "petal.width"]]),
            rtol=1e-03, atol=1e-03, equal_nan=False
        )))
