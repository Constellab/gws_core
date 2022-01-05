# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, Settings, TableDecoder, TableEncoder,
                      TaskRunner)
from gws_core_test_helper import GWSCoreTestHelper

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTableEncoding(BaseTestCase):

    async def test_table_encoding_decoding(self):
        # importer
        table = GWSCoreTestHelper.get_data_table()

        print(table)

        table_en = GWSCoreTestHelper.get_data_encoding_table()

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
