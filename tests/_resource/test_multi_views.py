# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from gws_core import ConfigParams, MultiViews, TextView, ViewType


# test_multi_views
class TestMultiViews(TestCase):

    def test_multi_view(self):
        view = TextView(data='Hello')

        text_view = TextView('Hello test super view')

        multi_view: MultiViews = MultiViews(4)
        multi_view.add_view(view, {}, 2, 1)
        multi_view.add_view(text_view, {}, 2, 1)
        multi_view.add_empty_block(2, 2)

        dict = multi_view.to_dict(ConfigParams())
        self.assertEqual(dict['type'], ViewType.MULTI_VIEWS.value)
        self.assertEqual(len(dict['data']["views"]), 3)
