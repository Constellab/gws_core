# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from pandas import DataFrame

from gws_core import Table, TableReplace


# test_table_replace
class TestTableTransposer(TestCase):

    def test_table_replace(self):
        initial_df = DataFrame({'A': [1, 2], 'B': ['Hello', 'Bonjour']})
        table = Table(data=initial_df)

        # Text multiple string to replace
        result: Table = TableReplace.call(table, {'replace_values': [
            {
                'search_value': 'Hello',
                'replace_value': 'Text',
                'is_regex': False
            },
            {
                'search_value': 'Bonjour',
                'replace_value': 'Text 2',
                'is_regex': False
            },
        ]})

        expected_result: DataFrame = DataFrame({'A': [1, 2], 'B': ['Text', 'Text 2']})
        self.assertTrue(result.get_data().equals(expected_result))

        # Text multiple string to replace using regex
        result_2: Table = TableReplace.call(table, {'replace_values': [
            {
                'search_value': '(Hello)|(Bonjour)',
                'replace_value': 'Text',
                'is_regex': True
            },
        ]})

        expected_result_2: DataFrame = DataFrame({'A': [1, 2], 'B': ['Text', 'Text']})
        self.assertTrue(result_2.get_data().equals(expected_result_2))

        # Text number replace
        result_3: Table = TableReplace.call(table, {'replace_values': [
            {
                'search_value': '1',
                'replace_value': 'Text',
                'is_regex': False
            },
        ]})

        expected_result_3: DataFrame = DataFrame({'A': ['Text', 2], 'B': ['Hello', 'Bonjour']})
        self.assertTrue(result_3.get_data().equals(expected_result_3))
