# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from unittest import IsolatedAsyncioTestCase

from gws_core.impl.table.action.table_column_action import (TableAddColumn,
                                                            TableRemoveColumn)
from gws_core.impl.table.table import Table
from pandas import DataFrame


# test_table_action
class TestTable(IsolatedAsyncioTestCase):

    def test_add_column(self):
        original_df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        table: Table = Table(original_df)

        add_column_action = TableAddColumn({"name": "C", "index": 2})
        # Test add a column
        table = add_column_action.execute(table)

        expected_df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [None, None, None]})
        self.assertTrue(table.get_data().equals(expected_df))

        # Test undo
        table = add_column_action.undo(table)
        self.assertTrue(table.get_data().equals(original_df))

    def test_remove_column(self):
        original_df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        table: Table = Table(original_df)

        remove_column_action = TableRemoveColumn({"name": "A"})
        # Test remove a column
        table = remove_column_action.execute(table)

        expected_df = DataFrame({"B": [4, 5, 6]})
        self.assertTrue(table.get_data().equals(expected_df))

        # Test undo
        table = remove_column_action.undo(table)
        self.assertTrue(table.get_data().equals(original_df))
