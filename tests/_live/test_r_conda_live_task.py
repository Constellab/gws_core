# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from pandas import DataFrame

from gws_core import File, RCondaLiveTask, TableImporter, TaskRunner
from gws_core.impl.table.table import Table
from gws_core.impl.table.tasks.table_exporter import TableExporter


# test_r_conda_live_task
class TestRCondaLiveTask(TestCase):

    def test_live_task_shell(self):
        dataframe = DataFrame({
            "one": [5.1, 4.9, 4.7, 4.6, 5.0],
            "two": [3.5, 3.0, 3.2, 3.1, 3.6],
        })
        table = Table(dataframe)

        result = TableExporter.call(
            table, params={"delimiter": ","})

        tester = TaskRunner(
            params={
                "code": """
# This is a snippet template for a R live task.

# retrieve the command line arguments
# Read the input csv file with column name
csv = read.csv(source_path, header = TRUE, sep = ",")

# Remove column named 'one'
csv_result = csv[, -which(names(csv) == "one")]

# Write the csv file into the result folder
write.csv(csv_result, file = paste(target_folder, "/result.csv", sep = ""), row.names = FALSE)
""",
                "env":
                """
name: .venv
channels:
- conda-forge
dependencies:
- r-base""",
            },
            inputs={"source": result},
            task_type=RCondaLiveTask
        )

        outputs = tester.run()
        target = outputs["target"]

        self.assertTrue(isinstance(target, File))

        table: Table = TableImporter.call(
            target, params={"delimiter": ",", "index_column": 0})

        # check that the column 'one' has been removed
        self.assertTrue(table.column_exists("two"))
        self.assertFalse(table.column_exists("one"))

        tester.run_after_task()
