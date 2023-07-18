# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from gws_core.config.config_params import ConfigParams
from gws_core.impl.file.file import File
from gws_core.impl.table.table import Table
from gws_core.impl.table.tasks.table_importer import TableImporter
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case_light import BaseTestCaseLight
from gws_core.test.data_provider import DataProvider


# test_excel_file
class TextExcelFile(BaseTestCaseLight):

    def test_view(self):
        file_path = DataProvider.get_test_data_path("small.xlsx")

        file = File(file_path)

        self.assertFalse(file.is_readable())
        self.assertIsNotNone(file.default_view(ConfigParams()))

    def test_import(self):

        file_path = DataProvider.get_test_data_path("small.xlsx")

        task_runner = TaskRunner(TableImporter, params={}, inputs={
                                 TableImporter.input_name: File(file_path)})

        outputs = task_runner.run()

        table: Table = outputs[TableImporter.output_name]

        self.assertIsNotNone(table)
        expected_df = DataFrame({'one': [5.1, 4.9], 'two': [
            'Setosa', 'Setosa'], 'three': ['Setosa', '1.4']})
        expected_table = Table(expected_df)
        self.assertTrue(table.equals(expected_table))
