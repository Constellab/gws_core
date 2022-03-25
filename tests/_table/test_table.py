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
from pandas import DataFrame

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTable(BaseTestCase):
    def test_table(self):
        table: Table = Table(data=[[1, 2, 3]], column_names=["a", "b", "c"])
        print(table.get_data())
        self.assertEqual(
            table.get_meta(),
            {'row_tags': [{}],
             'column_tags': [{},
                             {},
                             {}],
             'column_tag_types': {},
             'row_tag_types': {},
             'comments': ''})

        table._set_data(
            data=[1, 2, 3], column_names=["data"], row_names=["a", "b", "c"]
        )
        print(table.get_data())
        self.assertEqual(table.get_meta(), {'row_tags': [{}, {}, {}], 'column_tags': [
                         {}], 'column_tag_types': {}, 'row_tag_types': {}, 'comments': ''})
        print(print(table.get_meta()))

    def test_table_select(self):
        meta = {
            "row_tags": [
                {"lg": "EN", "c": "US", "user": "Vi"},
                {"lg": "JP", "c": "JP", "user": "Jo"},
                {"lg": "FR", "c": "FR", "user": "Jo"},
            ],
            "column_tags": [
                {"lg": "EN", "c": "UK"},
                {"lg": "PT", "c": "PT"},
                {"lg": "CH", "c": "CH"}
            ],
        }

        table: Table = Table(
            data=[[1, 2, 3], [3, 4, 6], [3, 7, 6]],
            row_names=["NY", "Tokyo", "Paris"],
            column_names=["London", "Lisboa", "Beijin"],
            meta=meta
        )
        self.assertEqual(table.get_meta(), meta)

        # ------------------------------------------------------------
        # Select by row positions
        # ------------------------------------------------------------

        t = table.select_by_row_positions([1, 2])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo", "Paris"])
        self.assertEqual(t.get_row_tags(), [
            {"lg": "JP", "c": "JP", "user": "Jo"},
            {"lg": "FR", "c": "FR", "user": "Jo"},
        ])
        self.assertEqual(t.get_column_tags(), [
            {"lg": "EN", "c": "UK"},
            {"lg": "PT", "c": "PT"},
            {"lg": "CH", "c": "CH"}
        ])

        # ------------------------------------------------------------
        # Select by column positions
        # ------------------------------------------------------------

        t = table.select_by_column_positions([0, 2])
        self.assertEqual(t.column_names, ["London", "Beijin"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])
        self.assertEqual(t.get_row_tags(), [
            {"lg": "EN", "c": "US", "user": "Vi"},
            {"lg": "JP", "c": "JP", "user": "Jo"},
            {"lg": "FR", "c": "FR", "user": "Jo"},
        ])
        self.assertEqual(t.get_column_tags(), [
            {"lg": "EN", "c": "UK"},
            {"lg": "CH", "c": "CH"}
        ])

        t = table.select_by_column_positions([2, 0])
        self.assertEqual(t.column_names, ["Beijin", "London"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])
        self.assertEqual(t.get_row_tags(), [
            {"lg": "EN", "c": "US", "user": "Vi"},
            {"lg": "JP", "c": "JP", "user": "Jo"},
            {"lg": "FR", "c": "FR", "user": "Jo"},
        ])
        self.assertEqual(t.get_column_tags(), [
            {"lg": "CH", "c": "CH"},
            {"lg": "EN", "c": "UK"},
        ])

        # ------------------------------------------------------------
        # Select by row names
        # ------------------------------------------------------------

        t = table.select_by_row_names(["Toky.*"], use_regex=True)
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo"])
        self.assertEqual(t.get_row_tags(), [
            {"lg": "JP", "c": "JP", "user": "Jo"},
        ])
        self.assertEqual(t.get_column_tags(), [
            {"lg": "EN", "c": "UK"},
            {"lg": "PT", "c": "PT"},
            {"lg": "CH", "c": "CH"}
        ])

        # ------------------------------------------------------------
        # Select by column names
        # ------------------------------------------------------------

        t = table.select_by_column_names(["L.*"], use_regex=True)
        self.assertEqual(t.column_names, ["London", "Lisboa"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])
        self.assertEqual(t.get_row_tags(), [
            {"lg": "EN", "c": "US", "user": "Vi"},
            {"lg": "JP", "c": "JP", "user": "Jo"},
            {"lg": "FR", "c": "FR", "user": "Jo"},
        ])
        self.assertEqual(t.get_column_tags(), [
            {"lg": "EN", "c": "UK"},
            {"lg": "PT", "c": "PT"},
        ])

        t = table.select_by_column_names(["L.*", "B.*"], use_regex=True)
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])

        t = table.select_by_row_names(["Tokyo", "Oui"])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo"])

        # ------------------------------------------------------------
        # Select by column tags
        # ------------------------------------------------------------

        t = table.select_by_column_tags([{"lg": "PT"}])
        self.assertEqual(t.column_names, ["Lisboa"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])

        t = table.select_by_column_tags([{"lg": "PT", "c": "PT"}])
        self.assertEqual(t.column_names, ["Lisboa"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])

        # ------------------------------------------------------------
        # Select by row tags
        # ------------------------------------------------------------

        # ( t1 )
        t = table.select_by_row_tags([{"c": "JP"}])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo"])

        # ( t2 )
        t = table.select_by_row_tags([{"user": "Jo"}])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo", "Paris"])

        # ( t1 AND t2 )
        t = table.select_by_row_tags([{"c": "JP", "user": "Jo"}])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo"])

        # ( t1 ) OR ( t2 )
        t = table.select_by_row_tags([{"user": "Jo"}, {"c": "JP"}])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo", "Paris"])

        # ( t1 AND t2 ) OR t2
        t = table.select_by_row_tags([{"user": "Jo", "c": "JP"}, {"c": "JP"}])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo"])

        # ( t1 AND t2 ) OR t1
        t = table.select_by_row_tags([{"user": "Jo", "c": "JP"}, {"user": "Jo"}])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["Tokyo", "Paris"])

    def test_table_import_1(self):

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
        # self.assertEqual(table.row_names, ["R0", "R1"])

    def test_table_import_2(self):

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
        # self.assertEqual(table.row_names, ["R0", "R1"])

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
        table.set_comments("This is a table")
        tester = TaskRunner(
            params={}, inputs={"source": table}, task_type=TableExporter
        )
        outputs = await tester.run()
        file_ = outputs["target"]

        print(file_.path)
        with open(file_.path, 'r') as fp:
            text = fp.read()
            print(text)
            self.assertTrue(text.startswith("#This is a table"))

        self.assertTrue(os.path.exists(file_.path))
