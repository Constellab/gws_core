# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List
from unittest import TestCase

from gws_core_test_helper import GWSCoreTestHelper

from gws_core import ViewTester
from gws_core.extra import TableVennDiagramView
from gws_core.impl.table.view.table_selection import Serie1d


# test_venn_diagram_view
class TestVennDiagrammView(TestCase):

    def test_venn_diagram_view(self,):
        table = GWSCoreTestHelper.get_venn_data_table()
        tester = ViewTester(
            view=TableVennDiagramView(table)
        )

        # 2 series :
        # first : y = A
        # second : y = B
        series: List[Serie1d] = [{"name": "first", "y": {"type": "columns", "selection": ["A"]}},
                                 {"name": "second", "y": {"type": "columns", "selection": ["B"]}}]
        dic = tester.to_dict({"series": series})
        self.assertEqual(dic["data"]["total_number_of_groups"], 2)
        self.assertEqual(len(dic["data"]["sections"]), 3)

        # 4 series :
        series: List[Serie1d] = [{"name": "first", "y": {"type": "columns", "selection": ["A"]}},
                                 {"name": "second", "y": {"type": "columns", "selection": ["B"]}},
                                 {"name": "third", "y": {"type": "columns", "selection": ["D"]}},
                                 {"name": "fourth", "y": {"type": "columns", "selection": ["E"]}},
                                 ]
        dic = tester.to_dict({"series": series})
        self.assertEqual(len(dic["data"]["sections"]), 15)
