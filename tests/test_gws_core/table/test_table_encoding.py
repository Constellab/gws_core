

from unittest import TestCase

from gws_core import TableDecoder, TableEncoder, TaskRunner
from gws_core.impl.table.table import Table

from ..gws_core_test_helper import GWSCoreTestHelper


# test_table_encoding
class TestTableEncoding(TestCase):

    def test_table_encoding_decoding(self):
        # importer
        table = GWSCoreTestHelper.get_small_data_table()

        table_en = GWSCoreTestHelper.get_data_encoding_table()

        # encoding
        tester = TaskRunner(
            task_type=TableEncoder,
            inputs={
                "table": table,
                "encoding_table": table_en,
            }
        )
        outputs = tester.run()
        etable: Table = outputs["encoded_table"]
        self.assertEqual(etable.row_names, ["oui", "non"])
        self.assertEqual(etable.column_names, ["B1", "C1", "D1", "E"])
        self.assertTrue((etable.get_data().values ==
                        table.get_data().values).all())

        # decoding
        tester = TaskRunner(
            task_type=TableDecoder,
            inputs={
                "encoded_table": etable,
                "encoding_table": table_en,
            }
        )
        outputs = tester.run()
        dtable: Table = outputs["decoded_table"]
        self.assertTrue(dtable.get_data().equals(table.get_data()))
