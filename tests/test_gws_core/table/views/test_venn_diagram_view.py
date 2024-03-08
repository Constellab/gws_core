# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List
from unittest import TestCase

from pandas import DataFrame

from gws_core import ViewTester
from gws_core.extra import TableVennDiagramView
from gws_core.impl.table.table import Table
from gws_core.impl.table.view.table_selection import Serie1d


# test_venn_diagram_view
class TestVennDiagrammView(TestCase):

    def test_venn_diagram_view(self,):

        # create dataframe from following table :
        # A	B	C	D	E
        # 1	2	3	4	1
        # a	3	c	a	2
        # 3	4	1	b
        # 	1	2	c
        dataframe = DataFrame({'A': [1, 'a', 3, None],
                               'B': [2, 3, 4, 1],
                               'C': [3, 'c', 1, 2],
                               'D': [4, 'a', None, 'c'],
                               'E': [1, 2, None, None]})

        # create table from dataframe
        table = Table(dataframe)

        tester = ViewTester(
            view=TableVennDiagramView(table)
        )

        # 2 series :
        # first : y = A
        # second : y = B
        series: List[Serie1d] = [{"name": "first", "y": {"type": "columns", "selection": ["A"]}},
                                 {"name": "second", "y": {"type": "columns", "selection": ["B"]}}]
        view_dto = tester.to_dto({"series": series})
        self.assertEqual(view_dto.data["total_number_of_groups"], 2)
        self.assertEqual(len(view_dto.data["sections"]), 3)

        # 4 series :
        series: List[Serie1d] = [{"name": "first", "y": {"type": "columns", "selection": ["A"]}},
                                 {"name": "second", "y": {
                                     "type": "columns", "selection": ["B"]}},
                                 {"name": "third", "y": {
                                     "type": "columns", "selection": ["D"]}},
                                 {"name": "fourth", "y": {
                                     "type": "columns", "selection": ["E"]}},
                                 ]
        view_dto = tester.to_dto({"series": series})
        self.assertEqual(len(view_dto.data["sections"]), 15)
