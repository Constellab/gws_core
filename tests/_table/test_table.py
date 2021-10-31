# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import pandas
from gws_core import (BaseTestCase, ConfigParams, TableExporter,
                      TableImporter, Table, File, GTest,
                      Settings, TaskModel, ConfigParams, TaskTester)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTable(BaseTestCase):
    def test_table(self):
        GTest.print("Table")

        table: Table = Table(data=[[1, 2, 3]], column_names=["a", "b", "c"])
        print(table.get_data())

        table._set_data(data=[1, 2, 3], column_names=["data"], row_names=["a", "b", "c"])
        print(table.get_data())

    def test_table_import(self):
        GTest.print("Table load")

        file_path = os.path.join(testdata_dir, "data.csv")
        table = Table.import_from_path(
            File(path=file_path),
            params=ConfigParams()
        )
        df = pandas.read_table(file_path)
        print(df)

        self.assertTrue(df.equals(table.get_data()))
        self.assertEqual(table.column_names, ["A", "B", "C", "D", "E"])
        self.assertEqual(table.row_names, [0, 1])

    async def test_importer_exporter(self):
        # importer
        file_path = os.path.join(testdata_dir, "data.csv")
        tester = TaskTester(
            params={},
            inputs = {'file': File(path=file_path)},
            task_type=TableImporter
        )
        self.assertTrue(os.path.exists(file_path))
        outputs = await tester.run()
        table = outputs["resource"]
        df = pandas.read_table(file_path)
        self.assertTrue(df.equals(table.get_data()))

        # exporter
        tester = TaskTester(
            params={},
            inputs = {'resource': table},
            task_type=TableExporter
        )
        outputs = await tester.run()
        file_ = outputs['file']

        print(file_.path)
        
        self.assertTrue(os.path.exists(file_.path))