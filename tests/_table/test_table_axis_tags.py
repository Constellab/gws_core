# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import IsolatedAsyncioTestCase

from gws_core.impl.table.table_axis_tags import TableAxisTags
from gws_core.test.base_test_case import BaseTestCase


class TestTableAxisTags(IsolatedAsyncioTestCase):

    def test_table_axis_tags(self):
        tags = TableAxisTags()

        self.assertEqual(tags.get_all_tags(), [])
        self.assertTrue(tags.all_tag_are_empty())

        tags.set_all_tags([{"a": "b"}, {"a": "d"}])
        self.assertEqual(tags.get_all_tags(), [{"a": "b"}, {"a": "d"}])

        tags.insert_new_empty_tags()
        self.assertEqual(tags.get_all_tags(), [{"a": "b"}, {"a": "d"}, {}])

        tags.add_tag_at(0, "new", "tag")
        self.assertEqual(tags.get_all_tags(), [{"a": "b", "new": "tag"}, {"a": "d"}, {}])

        self.assertEqual(tags.get_tags_between(0, 1), [{"a": "b", "new": "tag"},  {"a": "d"}])
        self.assertEqual(tags.get_tags_at(1), {"a": "d"})
        self.assertEqual(tags.get_tags_at_indexes([0, 1]), [{"a": "b", "new": "tag"}, {"a": "d"}])

        BaseTestCase.assert_json(tags.get_available_tags(), {"a": ["b", "d"], "new": ["tag"]})

        tags.set_tags_at(1, {"AA": "AA"})
        self.assertEqual(tags.get_tags_at(1), {"AA": "AA"})
