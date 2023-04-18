# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from unittest import TestCase

from pandas import DataFrame

from gws_core import Table, TableTagExtractorHelper


# test_table_tag_extractor
class TestTableTagAggregator(TestCase):

    def test_table_tag_extractor_helper(self):
        initial_df = DataFrame({'F1': [1, 2, 3, 4], 'F2': [7, 1, 10, 8], 'F3': [2, 1, 4, 2]})
        row_tags = [{'gender': 'M', 'age': '10'},
                    {'gender': 'F', 'age': '15'},
                    {'gender': 'M', 'age': '10'},
                    {'gender': 'F', 'age': '12'}]
        column_tags = [{'group': 'A'}, {'group': 'A'}, {'group': 'B'}]

        table = Table(initial_df, row_tags=row_tags, column_tags=column_tags)

        # Create a new column contaning the gender values
        result_table = TableTagExtractorHelper.extract_row_tags(table, key='gender')

        self.assertEqual(result_table.nb_columns, 4)
        self.assertEqual(result_table.get_data()['gender'].tolist(), ['M', 'F', 'M', 'F'])

        # Test creating a new column name 'test_age' with age as number
        result_table = TableTagExtractorHelper.extract_row_tags(
            table, key='age', tag_values_type='numeric', new_column_name='test_age')

        self.assertEqual(result_table.nb_columns, 4)
        self.assertEqual(result_table.get_data()['test_age'].tolist(), [10.0, 15.0, 10.0, 12.0])

        # Create a new row contaning the group values
        result_table = TableTagExtractorHelper.extract_column_tags(table, key='group')

        self.assertEqual(result_table.nb_rows, 5)
        self.assertEqual(result_table.get_data().iloc[4].tolist(), ['A', 'A', 'B'])
