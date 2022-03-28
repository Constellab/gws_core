
from gws_core import (EncodingTableImporter, File, MetadataTable,
                      MetadataTableImporter, Table, TableImporter)
from gws_core.data_provider.data_provider import DataProvider


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
    def get_sample_table(cls, index_column=0) -> Table:
        return TableImporter.call(File(DataProvider.get_test_data_path("sample_data.csv")), {
            "index_column": index_column,
            "header": 0,
        })

    @classmethod
    def get_sample_metadata_table(cls) -> MetadataTable:
        file = File(DataProvider.get_test_data_path("sample_metadata.csv"))
        print(file.path)
        return MetadataTableImporter.call(file)

    @classmethod
    def get_data_encoding_table(cls) -> Table:
        return EncodingTableImporter.call(File(DataProvider.get_test_data_path("data_encoding.csv")), {
            "original_column": "ocn",
            "original_row": "orn",
            "encoded_column": "ecn",
            "encoded_row": "ern",
        })

    @classmethod
    def get_venn_data_table(cls) -> Table:
        return TableImporter.call(File(DataProvider.get_test_data_path("venn_data.csv")), {
            "delimiter": "tab",
            "header": 0
        })
