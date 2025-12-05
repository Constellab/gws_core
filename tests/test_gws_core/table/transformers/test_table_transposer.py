from unittest import TestCase

from gws_core import Table
from pandas import DataFrame


# test_table_transposer
class TestTableTransposer(TestCase):
    def test(self):
        initial_df = DataFrame({"A": range(1, 5), "B": [10, 0, 6, 4]}, index=["0", "1", "2", "3"])

        table = Table(data=initial_df)
        row_tags = [
            {"gender": "M", "age": "10"},
            {"gender": "F", "age": "10"},
            {"gender": "F", "age": "10"},
            {"gender": "M", "age": "20"},
        ]
        column_tags = [{"test": "ok"}, {"test": "nok"}]
        table.set_all_row_tags(row_tags)
        table.set_all_column_tags(column_tags)

        transposed = table.transpose()
        self.assertTrue(transposed.get_data().equals(initial_df.T))
        self.assertEqual(transposed.get_row_tags(), column_tags)
        self.assertEqual(transposed.get_column_tags(), row_tags)

        re_transposed = transposed.transpose()

        self.assertTrue(re_transposed.get_data().equals(initial_df))
        self.assertEqual(re_transposed.get_row_tags(), row_tags)
        self.assertEqual(re_transposed.get_column_tags(), column_tags)
