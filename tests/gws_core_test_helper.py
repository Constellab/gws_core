
from gws_core import (EncodingTableImporter, File, MetadataTable,
                      MetadataTableImporter, Table, TableImporter)
from gws_core.test.data_provider import DataProvider


class GWSCoreTestHelper():

    @classmethod
    def get_small_data_file_path(cls, index=1) -> str:
        return DataProvider.get_test_data_path(f"small_data_{index}.csv")

    @classmethod
    def get_small_data_table(cls, index=1) -> Table:
        return TableImporter.call(File(cls.get_small_data_file_path(index)), {
            "index_column": 0,
            "header": 0,
        })

    @classmethod
    def get_data_encoding_table(cls) -> Table:
        return EncodingTableImporter.call(File(DataProvider.get_test_data_path("data_encoding.csv")), {
            "original_column": "ocn",
            "original_row": "orn",
            "encoded_column": "ecn",
            "encoded_row": "ern",
        })
