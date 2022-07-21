# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import numpy
import pandas
from gws_core import (BaseTestCase, File, Table, TableExporter, TableImporter,
                      TaskRunner)
from gws_core_test_helper import GWSCoreTestHelper
from pandas import DataFrame


class TestTable(BaseTestCase):
    def test_table(self):
        table: Table = Table(data=[[1, 2, 3]], column_names=["a", "b", "c"])

        self.assert_json(table.get_row_tags(), [{}])
        self.assert_json(table.get_column_tags(), [{}, {}, {}])
        self.assertEqual(table.comments, None)

    def test_create_sub_table(self):
        dataframe = DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        row_tags = [{'a': "1"}, {'a': "2"}, {'a': "3"}]
        column_tags = [{'b': "4"}, {'b': "5"}]

        table = Table(data=dataframe, row_tags=row_tags, column_tags=column_tags)

        # Simulate the filter by column B
        sub_dataframe = DataFrame({'A': [1, 2, 3]})

        sub_table = table.create_sub_table_filtered_by_columns(sub_dataframe)
        self.assertTrue(sub_table.get_data().equals(sub_dataframe.copy()))
        self.assertEqual(sub_table.get_row_tags(), row_tags)
        # there should be only one column --> one tag
        self.assertEqual(sub_table.get_column_tags(), [{'b': "4"}])

        # Simulate the filter by row 1 & 2
        sub_dataframe = DataFrame({'A': [1, 2], 'B': [4, 5]})

        sub_table = table.create_sub_table_filtered_by_rows(sub_dataframe)
        self.assertTrue(sub_table.get_data().equals(sub_dataframe.copy()))
        self.assertEqual(sub_table.get_column_tags(), column_tags)
        # there should be only two rows --> tow tag
        self.assertEqual(sub_table.get_row_tags(), [{'a': "1"}, {'a': "2"}])

    def test_table_select(self):
        row_tags = [
            {"lg": "EN", "c": "US", "user": "Vi"},
            {"lg": "JP", "c": "JP", "user": "Jo"},
            {"lg": "FR", "c": "FR", "user": "Jo"},
        ]
        column_tags = [
            {"lg": "EN", "c": "UK"},
            {"lg": "PT", "c": "PT"},
            {"lg": "CH", "c": "CH"}
        ]

        table: Table = Table(
            data=[[1, 2, 3], [3, 4, 6], [3, 7, 6]],
            row_names=["NY", "Tokyo", "Paris"],
            column_names=["London", "Lisboa", "Beijin"],
            row_tags=row_tags,
            column_tags=column_tags
        )

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
            {"lg": "EN", "c": "UK"},
            {"lg": "CH", "c": "CH"},
        ])

        # ------------------------------------------------------------
        # Select by row names
        # ------------------------------------------------------------

        t = table.select_by_row_names([{"name": ["Toky.*"], "is_regex": True}])
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

        t = table.select_by_column_names([{"name": ["L.*"], "is_regex": True}])
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

        t = table.select_by_column_names([{"name": ["L.*", "B.*"], "is_regex": True}])
        self.assertEqual(t.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(t.row_names, ["NY", "Tokyo", "Paris"])

        t = table.select_by_row_names([{"name": ["Tokyo", "Oui"]}])
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
        table: Table = TableImporter.call(File(file_path))
        df = pandas.read_table(file_path)

        self.assertTrue(numpy.array_equal(
            df.to_numpy(),
            table.get_data().to_numpy()
        ))
        self.assertEqual(table.column_names, ["A", "B", "C", "D", "E"])
        self.assertEqual(table.row_names, [0, 1])
        # self.assertEqual(table.row_names, ["R0", "R1"])

    def test_table_import_2(self):
        """ Test import with weird caracters and #"""

        file_path = GWSCoreTestHelper.get_small_data_file_path(2)
        table: Table = TableImporter.call(File(file_path), params={"comment": ""})

        df = table.get_data()
        self.assertEqual(df['A'][0], '#')
        self.assertEqual(df['B'][0], 'éçàùè$€')

    async def test_importer_exporter(self):
        # importer
        file_path = GWSCoreTestHelper.get_small_data_file_path(1)
        tester = TaskRunner(
            params={}, inputs={"source": File(path=file_path)}, task_type=TableImporter
        )
        self.assertTrue(os.path.exists(file_path))
        outputs = await tester.run()
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
        outputs = await tester.run()
        file_ = outputs["target"]

        with open(file_.path, 'r') as fp:
            text = fp.read()
            self.assertTrue(text.startswith("#This is a table"))

        self.assertTrue(os.path.exists(file_.path))

    async def test_generate_column_name(self):
        dataframe = DataFrame({'A': range(1, 6)})

        table = Table(data=dataframe)
        self.assertEqual(table.generate_new_column_name('Test'), 'Test')
        # test generating a new that already exists
        self.assertEqual(table.generate_new_column_name('A'), 'A_1')
