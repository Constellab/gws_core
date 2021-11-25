

import os

from gws_core import (ConfigParams, File, MultiViews, ScatterPlot2DView, Table,
                      TextView)
from gws_core.test.base_test_case import BaseTestCase


class TestMultiViews(BaseTestCase):

    def test_multi_view(self):
        testdata_dir = self.get_test_data_dir()
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(File(file_path), ConfigParams(delimiter=",", head=0, file_format='.csv'))
        view = ScatterPlot2DView(data=table)

        text_view = TextView('Hello test super view')

        multi_view: MultiViews = MultiViews(4)
        multi_view.add_view(view, {}, 2, 1)
        multi_view.add_view(text_view, {}, 2, 1)
        multi_view.add_empty_block(2, 2)

        dict = multi_view.to_dict(ConfigParams())
        self.assertEqual(dict['type'], 'multi-view')
        self.assertEqual(len(dict['data']["series"]), 3)
