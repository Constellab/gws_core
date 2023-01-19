# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import List
from unittest import TestCase

import numpy

from gws_core import BaseTestCase, ViewTester, ViewType
from gws_core.extra import DataProvider, TableHistogramView
from gws_core.impl.table.view.table_selection import Serie1d


class TestTableHistogramView(TestCase):
    def test_histogram_view(self,):
        pass

    # def test_histogram_view(self,):
    #     table = DataProvider.get_iris_table()
    #     tester = ViewTester(
    #         view=TableHistogramView(table)
    #     )

    #     # 2 series :
    #     # first : y = petal.length
    #     # second :  y = petal.width
    #     series: List[Serie1d] = [{"name": "first", "y": {"type": "columns", "selection": ["petal.length"]}},
    #                              {"name": "second", "y": {"type": "columns", "selection": ["petal.width"]}}
    #                              ]
    #     dic = tester.to_dict({"series": series})

    #     self.assertEqual(dic["type"], ViewType.HISTOGRAM.value)

    #     self.assertTrue(numpy.all(numpy.isclose(
    #         dic["data"]["series"][0]["data"]["y"],
    #         [37, 13, 0, 3, 8, 26, 29, 18, 11, 5],
    #         rtol=1e-03, atol=1e-03, equal_nan=False
    #     )))

    #     edges = numpy.array([1.0, 1.59, 2.18, 2.7700, 3.3600, 3.95, 4.5400, 5.1300, 5.7200, 6.3100, 6.9])
    #     edges_centers = (edges[0:-2] + edges[1:-1])/2
    #     self.assertTrue(numpy.all(numpy.isclose(
    #         dic["data"]["series"][0]["data"]["x"],
    #         edges_centers,
    #         rtol=1e-05, atol=1e-03, equal_nan=False
    #     )))

    #     self.assertTrue(numpy.all(numpy.isclose(
    #         dic["data"]["series"][1]["data"]["y"],
    #         [41, 8, 1, 7, 8, 33, 6, 23, 9, 14],
    #         rtol=1e-03, atol=1e-03, equal_nan=False
    #     )))

    #     edges = numpy.array([0.1, 0.3399, 0.58, 0.82, 1.06, 1.3, 1.54, 1.78, 2.02, 2.260, 2.5])
    #     edges_centers = (edges[0:-2] + edges[1:-1])/2
    #     self.assertTrue(numpy.all(numpy.isclose(
    #         dic["data"]["series"][1]["data"]["x"],
    #         edges_centers,
    #         rtol=1e-05, atol=1e-03, equal_nan=False
    #     )))
