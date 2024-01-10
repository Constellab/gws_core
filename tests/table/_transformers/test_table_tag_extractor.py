# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from unittest import TestCase

from pandas import DataFrame

from gws_core import Table


# test_table_tag_extractor
class TestTableTagAggregator(TestCase):

    def test_extract_row_tags_to_new_columns(self):
        initial_df = DataFrame({'F1': [1, 2], 'F2': [3, 4]})
        row_tags = [{'gender': 'M', 'age': '10'},
                    {'gender': 'F', 'age': '15'}]

        table = Table(initial_df, row_tags=row_tags)

        # Create a new column contaning the gender values
        table.extract_row_tags_to_new_column('gender')

        self.assertEqual(table.nb_columns, 3)
        self.assertEqual(table.nb_rows, 2)
        self.assertEqual(table.get_column_data('gender'), ['M', 'F'])

    def test_extract_columns_tags_to_new_row(self):
        initial_df = DataFrame({'F1': [1, 2], 'F2': [3, 4]})
        column_tags = [{'group': 'A'}, {'group': 'A'}]

        # Create a new row contaning the group values
        table = Table(initial_df, column_tags=column_tags)
        table.extract_column_tags_to_new_row('group')

        self.assertEqual(table.nb_rows, 3)
        self.assertEqual(table.nb_columns, 2)
        self.assertEqual(table.get_row_data('group'), ['A', 'A'])

    def test_extract_row_values_to_column_tags(self):
        initial_df = DataFrame({'F1': [1, 2], 'F2': [3, 4]})

        table = Table(initial_df)
        table.extract_row_values_to_column_tags('0')

        self.assertEqual(table.nb_rows, 2)
        self.assertEqual(table.nb_columns, 2)
        self.assertEqual(table.get_column_tags(), [{'0': '1'}, {'0': '3'}])

    def test_extract_column_values_to_row_tags(self):
        initial_df = DataFrame({'F1': [1, 2], 'F2': [3, 4]})

        table = Table(initial_df)
        table.extract_column_values_to_row_tags('F1')

        self.assertEqual(table.nb_rows, 2)
        self.assertEqual(table.nb_columns, 2)
        self.assertEqual(table.get_row_tags(), [{'F1': '1'}, {'F1': '2'}])
