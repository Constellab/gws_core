# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from gws_core import (BaseTestCase, File, RCondaLiveTask, ResourceSet,
                      TableImporter, TaskRunner)


# test_r_conda_live_task
class TestRCondaLiveTask(BaseTestCase):

    def test_live_task_shell(self):
        print("Skip the tests of RCondaLiveTask")
        print("Please uncomment code to activate the test. This may take a while!")
        return

        file_set = ResourceSet()
        file = File(path="./foo/bar")
        file.name = "my_file"
        file_set.add_resource(file)

        tester = TaskRunner(
            params={
                "code": """
                                print("Hello, world!")
                                d <- read.table(text=
                                'Name     Month  Rate1     Rate2
                                Aira       0      12        23
                                Aira       0      12        23
                                Aira       0      12        23
                                Ben        1      10        4
                                Ben        2      8         2
                                Cat        1      3        18
                                Cat        1      6        0
                                Cat        1      0        0', header=TRUE)
                                table = aggregate(d[, 3:4], list(d$Name), mean)
                                write.csv(table,"table.csv", row.names = TRUE)
                                """,
                "args": "",
                "env":
                """name: .venv
channels:
- conda-forge
dependencies:
- r-base""",
                "output_file_paths": ["table.csv"]
            },
            inputs={"source": file_set},
            task_type=RCondaLiveTask
        )

        outputs = tester.run()
        target = outputs["target"]
        self.assertTrue(isinstance(target, ResourceSet))

        resources = target.get_resources()

        file = resources["table.csv"]
        self.assertTrue(isinstance(file, File))
        print(file.read().strip())

        table = TableImporter.call(file, params={"delimiter": ",", "index_column": 0})

        df = DataFrame(
            data=[
                ["Aira", 12, 23],
                ["Ben", 9, 3],
                ["Cat", 3, 6]
            ],
            index=[1, 2, 3],
            columns=["Group.1", "Rate1", "Rate2"]
        )

        self.assertTrue(table.get_data().equals(df))
