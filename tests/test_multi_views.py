

from gws_core import ConfigParams, MultiViews, TableScatterPlot2DView, TextView
from gws_core.extra import DataProvider
from gws_core.test.base_test_case import BaseTestCase


class TestMultiViews(BaseTestCase):

    def test_multi_view(self):
        table = DataProvider.get_iris_table()
        view = TableScatterPlot2DView(data=table)

        text_view = TextView('Hello test super view')

        multi_view: MultiViews = MultiViews(4)
        multi_view.add_view(view, {}, 2, 1)
        multi_view.add_view(text_view, {}, 2, 1)
        multi_view.add_empty_block(2, 2)

        dict = multi_view.to_dict(ConfigParams())
        self.assertEqual(dict['type'], 'multi-view')
        self.assertEqual(len(dict['data']["views"]), 3)
