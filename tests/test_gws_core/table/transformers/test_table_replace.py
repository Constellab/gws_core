

from unittest import TestCase

from pandas import DataFrame

from gws_core import Table, TableReplace


# test_table_replace
class TestTableReplace(TestCase):

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

        expected_result: DataFrame = Table(DataFrame({'A': [1, 2], 'B': ['Text', 'Text 2']}))
        self.assertTrue(result.equals(expected_result))

        # Text multiple string to replace using regex
        result_2: Table = TableReplace.call(table, {'replace_values': [
            {
                'search_value': '(Hello)|(Bonjour)',
                'replace_value': 'Text',
                'is_regex': True
            },
        ]})

        expected_result_2: DataFrame = Table(DataFrame({'A': [1, 2], 'B': ['Text', 'Text']}))
        self.assertTrue(result_2.equals(expected_result_2))

        # Text number replace
        result_3: Table = TableReplace.call(table, {'replace_values': [
            {
                'search_value': '1',
                'replace_value': 'Text',
                'is_regex': False
            },
        ]})

        expected_result_3: DataFrame = Table(DataFrame({'A': ['Text', 2], 'B': ['Hello', 'Bonjour']}))
        self.assertTrue(result_3.equals(expected_result_3))
