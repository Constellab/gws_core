import os

import numpy
from pandas import DataFrame
from gws_core import BaseTestCase, HeatmapView, Settings, Table, ViewTester, ConfigParams, File


class TestHeatmapView(BaseTestCase):

    def test_heatmap_view(self,):
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
            view = HeatmapView(table)
        )
        dic = tester.to_dict({
            "from_column":1,
            "number_of_columns_per_page":4,
            "scale":"none"
        })
        self.assertEqual(dic["type"], "heatmap-view")
        self.assertEqual(
            dic["data"],
            table.to_table().iloc[0:50, 0:4].to_dict('list')
        )

        data = table.get_data().iloc[0:50, 0:4]
        data = DataFrame(
            data=numpy.log10(data),
            index=data.index,
            columns=data.columns
        )
        dic = tester.to_dict({
            "from_column":1, 
            "number_of_columns_per_page":4, 
            "scale":"log10"
        })
        self.assertEqual(
            dic["data"],
            data.to_dict('list')
        )