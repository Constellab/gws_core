# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, ConfigParams, EncodingTable, File, GTest,
                      Settings, Table, TableDecoder, TableEncoder,
                      TableExporter, TableFilter, TableImporter, TaskModel,
                      TaskRunner)

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
        table_en = EncodingTable.import_from_path(File(path=file_path), params=ConfigParams({
            "original_column": "ocn",
            "original_row": "orn",
            "encoded_column": "ecn",
            "encoded_row": "ern",
        }))

        # encoding
        tester = TaskRunner(
            task_type=TableEncoder,
            inputs={
                "table": table,
                "encoding_table": table_en,
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
                "encoding_table": table_en,
            }
        )
        outputs = await tester.run()
        dtable = outputs["decoded_table"]
        self.assertTrue(dtable.get_data().equals(table.get_data()))
