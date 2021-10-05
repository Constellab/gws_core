import os

import numpy
from gws_core import BaseTestCase, HistogramView, Settings, Table


class TestHistogramView(BaseTestCase):

    def test_histogram_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(file_path, delimiter=",", head=0)
        vw = HistogramView(table, ["petal.length", "petal.width"])

        dic = vw.to_dict()

        print(dic)

        self.assertEqual(dic["type"], "histogram")

        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][0]["data"]["hist"],
            [37, 13, 0, 3, 8, 26, 29, 18, 11, 5],
            rtol=1e-03, atol=1e-03, equal_nan=False
        )))

        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][0]["data"]["bin_edges"],
            [1.0, 1.59, 2.18, 2.7700, 3.3600, 3.95, 4.5400, 5.1300, 5.7200, 6.3100, 6.9],
            rtol=1e-05, atol=1e-03, equal_nan=False
        )))

        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][1]["data"]["hist"],
            [41, 8, 1, 7, 8, 33, 6, 23, 9, 14],
            rtol=1e-03, atol=1e-03, equal_nan=False
        )))

        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][1]["data"]["bin_edges"],
            [0.1, 0.3399, 0.58, 0.82, 1.06, 1.3, 1.54, 1.78, 2.02, 2.260, 2.5],
            rtol=1e-05, atol=1e-03, equal_nan=False
        )))
