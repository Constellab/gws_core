import inspect
import os
import numpy
from typing import List

from gws_core import (BaseTestCase, Resource, ResourceService, Robot, Settings,
                      Table, HeatmapView, resource_decorator, view)
from pandas import DataFrame


class TestHeatmapView(BaseTestCase):

    def test_heatmap_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(file_path, delimiter=",", head=0)
        vw = HeatmapView(table)

        dic = vw.to_dict(
            column_names=["petal.length","petal.width"],
            title="my title",
            subtitle="my subtitle"
        )

        self.assertEqual(dic["type"], "heatmap")
        self.assertEqual(dic["title"], "my title")
        self.assertEqual(dic["subtitle"], "my subtitle")
        
        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][0]["data"],
            table.get_data()[["petal.length","petal.width"]], 
            rtol=1e-03, atol=1e-03, equal_nan=False
        )))

        dic = vw.to_dict(
            column_names=["petal.length","petal.width"],
            scale="log10",
            title="my title",
            subtitle="my subtitle"
        )
        self.assertTrue(numpy.all(numpy.isclose(
            dic["series"][0]["data"],
            numpy.log10(table.get_data()[["petal.length","petal.width"]]), 
            rtol=1e-03, atol=1e-03, equal_nan=False
        )))
