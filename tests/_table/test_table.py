# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import numpy
import pandas
from gws_core import (BaseTestCase, File, GTest, Settings, Table,
                      TableExporter, TableImporter, TaskRunner)
from gws_core_test_helper import GWSCoreTestHelper

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
        t = table.select_by_row_positions([1, 2])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo", "Paris"])

        t = table.select_by_column_positions([0, 2])
        self.assertEqual(t.column_names, ["London", "Beijin"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])

        t = table.select_by_row_names(["Toky.*"], use_regex=True)
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo"])

        t = table.select_by_column_names(["L.*"], use_regex=True)
        self.assertEqual(t.column_names, ["London", "Lisboa"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])

        t = table.select_by_column_names(["L.*", "B.*"], use_regex=True)
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])

        t = table.select_by_row_names(["Tokyo", "Oui"])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo"])

        print(t)

    def test_table_import_1(self):
        GTest.print("Table load")

        file_path = GWSCoreTestHelper.get_small_data_file_path(1)
        table = TableImporter.call(File(file_path))
        df = pandas.read_table(file_path)
        print(df)

        self.assertTrue(numpy.array_equal(
            df.to_numpy(),
            table.get_data().to_numpy()
        ))
        self.assertEqual(table.column_names, ["A", "B", "C", "D", "E"])
        self.assertEqual(table.row_names, [0, 1])
        #self.assertEqual(table.row_names, ["R0", "R1"])

    def test_table_import_2(self):
        GTest.print("Table load")

        file_path = GWSCoreTestHelper.get_small_data_file_path(2)
        table = TableImporter.call(File(file_path))
        df = pandas.read_table(file_path)
        print(df)

        self.assertTrue(numpy.array_equal(
            df.to_numpy(),
            table.get_data().to_numpy()
        ))
        self.assertEqual(table.column_names, ["A", "B", "3", "D", "1.5"])
        self.assertEqual(table.row_names, [0, 1])
        #self.assertEqual(table.row_names, ["R0", "R1"])

    async def test_importer_exporter(self):
        # importer
        file_path = GWSCoreTestHelper.get_small_data_file_path(1)
        tester = TaskRunner(
            params={}, inputs={"source": File(path=file_path)}, task_type=TableImporter
        )
        self.assertTrue(os.path.exists(file_path))
        outputs = await tester.run()
        table = outputs["target"]
        df = pandas.read_table(file_path)
        self.assertTrue(numpy.array_equal(
            df.to_numpy(),
            table.get_data().to_numpy()
        ))

        # exporter
        tester = TaskRunner(
            params={}, inputs={"source": table}, task_type=TableExporter
        )
        outputs = await tester.run()
        file_ = outputs["target"]

        print(file_.path)
        self.assertTrue(os.path.exists(file_.path))
