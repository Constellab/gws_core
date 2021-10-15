import os

import numpy
from gws_core import BaseTestCase, BoxPlotView, Settings, Table


class TestBoxPlotView(BaseTestCase):

    def test_boxplot_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(file_path, delimiter=",", head=0)
        
        vw = BoxPlotView(table)
        dic = vw.to_dict(column_names=["petal.length", "petal.width"])
        self.assertEqual(dic["type"], "box-plot")
        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][0]["data"]["min"],
            [1.0, 0.1],
            rtol=1e-03, atol=1e-03, equal_nan=False
        )))
        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][0]["data"]["median"],
            [4.35, 1.3],
            rtol=1e-03, atol=1e-03, equal_nan=False
        )))
        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][0]["data"]["q3"],
            [5.1, 1.8],
            rtol=1e-03, atol=1e-03, equal_nan=False
        )))

