from typing import cast
from unittest import TestCase

from gws_core import Table, TableReplace
from gws_core.config.config_params import ConfigParamsDict
from gws_core.task.task_runner import TaskRunner
from numpy import nan
from pandas import DataFrame


# test_table_replace
class TestTableReplace(TestCase):
    def _run_replace(self, table: Table, config: ConfigParamsDict) -> Table:
        task_runner = TaskRunner(TableReplace, config, inputs={TableReplace.input_name: table})
        return cast(Table, task_runner.run()[TableReplace.output_name])

    def test_table_replace(self):
        initial_df = DataFrame({"A": [1, 2], "B": ["Hello", "Bonjour"]})
        table = Table(data=initial_df)

        # Text multiple string to replace
        result = self._run_replace(
            table,
            {
                "replace_values": [
                    {"search_value": "Hello", "replace_value": "Text", "is_regex": False},
                    {"search_value": "Bonjour", "replace_value": "Text 2", "is_regex": False},
                ]
            },
        )

        expected_result: Table = Table(DataFrame({"A": [1, 2], "B": ["Text", "Text 2"]}))
        self.assertTrue(result.equals(expected_result))

        # Text multiple string to replace using regex
        result = self._run_replace(
            table,
            {
                "replace_values": [
                    {
                        "search_value": "(Hello)|(Bonjour)",
                        "replace_value": "Text",
                        "is_regex": True,
                    },
                ]
            },
        )

        expected_result_2: Table = Table(DataFrame({"A": [1, 2], "B": ["Text", "Text"]}))
        self.assertTrue(result.equals(expected_result_2))

        # Text number replace
        result = self._run_replace(
            table,
            {
                "replace_values": [
                    {"search_value": "1", "replace_value": "Text", "is_regex": False},
                ]
            },
        )

        expected_result_3: Table = Table(
            DataFrame({"A": ["Text", 2], "B": ["Hello", "Bonjour"]})
        )
        self.assertTrue(result.equals(expected_result_3))

    def test_replace_none(self):
        initial_df = DataFrame({"A": [None, nan, "Bonjour"]})
        table = Table(data=initial_df)

        # Replace None
        result = self._run_replace(
            table,
            {
                "replace_values": [
                    {"search_value": "None", "replace_value": "Hello", "is_regex": False},
                ]
            },
        )

        expected_result: Table = Table(DataFrame({"A": ["Hello", "Hello", "Bonjour"]}))
        self.assertTrue(result.equals(expected_result))
