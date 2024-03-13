

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

        view_dto = multi_view.to_dto(ConfigParams())
        self.assertEqual(view_dto.type, ViewType.MULTI_VIEWS)
        self.assertEqual(len(view_dto.data["views"]), 3)
