# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from unittest import TestCase

import numpy
import pandas

from gws_core import File, Table, TableExporter, TableImporter, TaskRunner

from ..gws_core_test_helper import GWSCoreTestHelper


# test_table_importer
class TestTableImporter(TestCase):
    def test_table_import_1(self):

        file_path = GWSCoreTestHelper.get_small_data_file_path(1)
        table: Table = TableImporter.call(File(file_path))
        df = pandas.read_table(file_path)

        self.assertTrue(numpy.array_equal(
            df.to_numpy(),
            table.get_data().to_numpy()
        ))
        self.assertEqual(table.column_names, ["A", "B", "C", "D", "E"])
        self.assertEqual(table.row_names, ['0', '1'])

    def test_table_import_2(self):
        """ Test import with weird caracters and #"""

        file_path = GWSCoreTestHelper.get_small_data_file_path(2)
        table: Table = TableImporter.call(
            File(file_path), params={"comment": ""})

        df = table.get_data()
        self.assertEqual(df['A'][0], '#')
        self.assertEqual(df['B'][0], 'éçàùè$€')

    def test_importer_exporter(self):
        # importer
        file_path = GWSCoreTestHelper.get_small_data_file_path(1)
        tester = TaskRunner(
            params={}, inputs={"source": File(path=file_path)}, task_type=TableImporter
        )
        self.assertTrue(os.path.exists(file_path))
        outputs = tester.run()
        table: Table = outputs["target"]
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
        outputs = tester.run()
        file_: File = outputs["target"]

        with open(file_.path, 'r') as fp:
            text = fp.read()
            self.assertTrue(text.startswith("#This is a table"))

        self.assertTrue(os.path.exists(file_.path))
