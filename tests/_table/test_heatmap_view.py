import os

import numpy
from gws_core import BaseTestCase, HeatmapView, ViewTester
from pandas import DataFrame
from tests.gws_core_test_helper import GwsCoreTestHelper


class TestTableHeatmapView(BaseTestCase):

    def test_heatmap_view(self,):
        table = await GwsCoreTestHelper.get_iris_table()
        tester = ViewTester(
            view=HeatmapView(table)
        )
        dic = tester.to_dict({
            "from_row": 1,
            "number_of_rows_per_page": 50,
            "from_column": 1,
            "number_of_columns_per_page": 4,
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
