# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import pandas
from gws_core import (BaseTestCase, ConfigParams, File, GTest, MetadataTable,
                      Settings, Table, TableAnnotator, TableDecoder,
                      TableExporter, TableFilter, TableImporter, TaskModel,
                      TaskRunner)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTableAnnotator(BaseTestCase):

    async def test_table_encoding_decoding(self):
        # importer
        file_path = os.path.join(testdata_dir, "data.csv")
        table = Table.import_from_path(File(path=file_path), params=ConfigParams({
            "index_columns": [0],
            "header": 0,
        }))

        file_path = os.path.join(testdata_dir, "metadata.csv")
        metatable = MetadataTable.import_from_path(File(path=file_path), params=ConfigParams({
            "index_columns": [0],
            "header": 0,
        }))
        print(table)

        # annotation
        tester = TaskRunner(
            task_type=TableAnnotator,
            inputs={
                "table": table,
                "metadata_table": metatable,
            }
        )
        outputs = await tester.run()
        annotated_table = outputs["annotated_table"]
        print(annotated_table)

        self.assertEqual(annotated_table.row_names, table.row_names)
        self.assertEqual(annotated_table.column_names, [
            "Sex:F|Group:15|Age:15",
            "Sex:M|Group:15|Age:15",
            "Sex:F|Group:3|Age:15",
            "Sex:F|Group:15|Age:15"
        ])
        self.assertTrue((annotated_table.get_data().values == table.get_data().values).all())
