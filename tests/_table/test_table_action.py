# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from unittest import IsolatedAsyncioTestCase

from pandas import DataFrame

from gws_core.impl.table.action.table_cell_action import TableUpdateCell
from gws_core.impl.table.action.table_column_action import (TableAddColumn,
                                                            TableRemoveColumn)
from gws_core.impl.table.table import Table


# test_table_action
class TestTable(IsolatedAsyncioTestCase):

    def test_add_column(self):
        original_df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        table: Table = Table(original_df)

        add_column_action = TableAddColumn({"name": "C", "index": 2})
        # Test add a column
        table = add_column_action.execute(table)

        expected = Table(DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [None, None, None]}))
        self.assertTrue(table.equals(expected))

        # Test undo
        table = add_column_action.undo(table)
        self.assertTrue(table.get_data().equals(original_df))

    def test_remove_column(self):
        original_df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        table: Table = Table(original_df)

        remove_column_action = TableRemoveColumn({"name": "A"})
        # Test remove a column
        table = remove_column_action.execute(table)

        expected = Table(DataFrame({"B": [4, 5, 6]}))
        self.assertTrue(table.equals(expected))

        # Test undo
        table = remove_column_action.undo(table)
        self.assertTrue(table.get_data().equals(original_df))

    def test_update_cell(self):
        original_df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        table: Table = Table(original_df)

        update_cell_action = TableUpdateCell({"row": 0, "column": 1, "new_value": 10})
        # Test update a cell
        table = update_cell_action.execute(table)

        expected = Table(DataFrame({"A": [1, 2, 3], "B": [10, 5, 6]}))
        self.assertTrue(table.equals(expected))

        # Test undo
        table = update_cell_action.undo(table)
        self.assertTrue(table.get_data().equals(original_df))
