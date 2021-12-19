# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import pandas
from gws_core import (BaseTestCase, File, GTest, Settings, Table,
                      TableExporter, TableImporter, TaskRunner)
from tests.gws_core_test_helper import GWSCoreTestHelper

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTable(BaseTestCase):
    def test_table(self):
        GTest.print("Table")

        table: Table = Table(data=[[1, 2, 3]], column_names=["a", "b", "c"])
        print(table.get_data())

        table._set_data(
            data=[1, 2, 3], column_names=["data"], row_names=["a", "b", "c"]
        )
        print(table.get_data())

    def test_table_select(self):
        GTest.print("Table select")

        table: Table = Table(
            data=[[1, 2, 3], [3, 4, 6], [3, 7, 6]],
            column_names=["London", "Lisboa", "Beijin"],
            row_names=["NY", "Tokyo", "Paris"]
        )
        t = table.select_by_row_indexes([1, 2])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo", "Paris"])

        t = table.select_by_column_indexes([0, 2])
        self.assertEqual(t.column_names, ["London", "Beijin"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])

        t = table.select_by_row_name("Toky.*")
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo"])

        t = table.select_by_column_name("L.*")
        self.assertEqual(t.column_names, ["London", "Lisboa"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])

        print(t)

    def test_table_import(self):
        GTest.print("Table load")

        file_path = GWSCoreTestHelper.get_data_file_path()
        table = TableImporter.call(File(file_path))
        df = pandas.read_table(file_path)
        print(df)

        self.assertTrue(df.equals(table.get_data()))
        self.assertEqual(table.column_names, ["A", "B", "C", "D", "E"])
        self.assertEqual(table.row_names, [0, 1])

    async def test_importer_exporter(self):
        # importer
        file_path = GWSCoreTestHelper.get_data_file_path()
        tester = TaskRunner(
            params={}, inputs={"source": File(path=file_path)}, task_type=TableImporter
        )
        self.assertTrue(os.path.exists(file_path))
        outputs = await tester.run()
        table = outputs["target"]
        df = pandas.read_table(file_path)
        self.assertTrue(df.equals(table.get_data()))

        # exporter
        tester = TaskRunner(
            params={}, inputs={"source": table}, task_type=TableExporter
        )
        outputs = await tester.run()
        file_ = outputs["target"]

        print(file_.path)

        self.assertTrue(os.path.exists(file_.path))
