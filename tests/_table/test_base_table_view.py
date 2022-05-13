# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, Table, ViewTester
from gws_core.impl.table.view.base_table_view import (BaseTableView, CellRange,
                                                      TableSelection)
from pandas import DataFrame


class TestTableView(BaseTestCase):

    def test_base_table_view(self):
        a_values = [1, 2, 3, 4, 5]
        b_values = [10, 8, 6, 4, 2]
        dataframe = DataFrame({'A': a_values, 'B': b_values})

        row_tags = [{'tag_1': '1'}, {'tag_2': '2'}, {'tag_3': '3'}, {'tag_4': '4'}, {'tag_5': '5'}]
        table = Table(dataframe, meta={"row_tags": row_tags})

        # get_values_from_columns
        base_view = BaseTableView(table)
        self.assertEqual(base_view.get_values_from_columns(['A', 'B']), a_values + b_values)

        # get_dataframe_from_columns
        self.assertTrue(dataframe.equals(base_view.get_dataframe_from_columns(['A', 'B'])))

        # get_values_from_coords
        # Expected value : [2, 3, 8, 6]
        cell_range: CellRange = {"from": {"row": 1, "column": 0}, "to": {"row": 2, "column": 1}}

        # Selection of a single cell column= 0 row=3 --> value = 4
        cell_range_2: CellRange = {"from": {"row": 3, "column": 0}, "to": {"row": 3, "column": 0}}
        self.assertEqual(base_view.get_values_from_coords([cell_range, cell_range_2]), [2, 3, 8, 6, 4])

        # get_dataframe_from_coords
        self.assertTrue(base_view.get_dataframe_from_coords(cell_range).equals(dataframe.iloc[1:3, 0:2]))

        selection_range: TableSelection = {"type": "range", "selection": [cell_range, cell_range_2]}
        self.assertEqual(base_view.get_values_from_selection_range(selection_range), [2, 3, 8, 6, 4])
        self.assertEqual(base_view.get_row_tags_from_selection_range(
            selection_range), [row_tags[1], row_tags[2], row_tags[3]])

        column_selection: TableSelection = {"type": "column", "selection": ['A', 'B']}
        self.assertEqual(base_view.get_values_from_selection_range(column_selection), a_values + b_values)
        self.assertEqual(base_view.get_row_tags_from_selection_range(column_selection), row_tags)
