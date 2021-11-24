# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import pandas
from gws_core import (BaseTestCase, ConfigParams, File, GTest, Settings, Table,
                      TableDecoder, TableEncoder, TableEncoding, TableExporter,
                      TableFilter, TableImporter, TaskModel, TaskRunner)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTableEncoding(BaseTestCase):

    async def test_table_encoding_decoding(self):
        # importer
        file_path = os.path.join(testdata_dir, "data.csv")
        table = Table.import_from_path(File(path=file_path), params=ConfigParams({
            "index_columns": [0],
            "header": 0,
        }))
        print(table)

        file_path = os.path.join(testdata_dir, "data_encoding.csv")
        table_en = TableEncoding.import_from_path(File(path=file_path), params=ConfigParams({
            "original_column_name": "ocn",
            "original_row_name": "orn",
            "encoded_column_name": "ecn",
            "encoded_row_name": "ern",
        }))

        # encoding
        tester = TaskRunner(
            task_type=TableEncoder,
            inputs={
                "table": table,
                "table_encoding": table_en,
            }
        )
        outputs = await tester.run()
        etable = outputs["encoded_table"]
        self.assertEqual(etable.row_names, ["oui", "non"])
        self.assertEqual(etable.column_names, ["B1", "C1", "D1", "E"])
        self.assertTrue((etable.get_data().values == table.get_data().values).all())

        # decoding
        tester = TaskRunner(
            task_type=TableDecoder,
            inputs={
                "encoded_table": etable,
                "table_encoding": table_en,
            }
        )
        outputs = await tester.run()
        dtable = outputs["decoded_table"]
        self.assertTrue(dtable.get_data().equals(table.get_data()))
