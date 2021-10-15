import os

import numpy
from pandas import DataFrame
from gws_core import BaseTestCase, HeatmapView, Settings, Table


class TestHeatmapView(BaseTestCase):

    def test_heatmap_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(file_path, delimiter=",", head=0)
        vw = HeatmapView(table)

        dic = vw.to_dict()
        self.assertEqual(dic["type"], "heatmap")
        self.assertEqual(
            dic["data"],
            table.to_table().iloc[0:49, 0:4].to_dict('list')
        )

        data = table.get_data().iloc[0:49, 0:4]
        data = DataFrame(
            data=numpy.log10(data), 
            index=data.index, 
            columns=data.columns
        )
        self.assertEqual(
            vw.to_dict(scale="log10")["data"],
            data.to_dict('list')
        )
