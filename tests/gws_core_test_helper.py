

import os

from gws_core import (AnnotatedTableImporter, Dataset, DatasetImporter,
                      EncodingTableImporter, File, MetadataTableImporter,
                      Settings, Table, TableImporter)


class GWSCoreTestHelper():

    @classmethod
    def get_test_data_dir(cls) -> str:
        return Settings.retrieve().get_variable("gws_core:testdata_dir")

    @classmethod
    def get_test_data_path(cls, *path: str) -> str:
        return os.path.join(cls.get_test_data_dir(), *path)

    @classmethod
    def get_iris_file(cls) -> File:
        return File(cls.get_test_data_path('iris.csv'))

    @classmethod
    def get_no_head_iris_file(cls) -> File:
        return File(cls.get_test_data_path('iris_no_head.csv'))

    @classmethod
    def get_iris_table(cls) -> Table:
        return TableImporter.call(cls.get_iris_file(), {
            "delimiter": ",",
            "header": 0
        })

    @classmethod
    def get_iris_dataset(cls) -> Dataset:
        return DatasetImporter.call(cls.get_iris_file(), {
            "delimiter": ",",
            "header": 0,
            "targets": ["variety"]
        })

    @classmethod
    def get_no_head_iris_dataset(cls) -> Dataset:
        return DatasetImporter.call(cls.get_no_head_iris_file(), {
            "delimiter": ",",
            "header": -1,
            "targets": [4]
        })

    @classmethod
    def get_data_file_path(cls) -> str:
        return cls.get_test_data_path("data.csv")

    @classmethod
    def get_data_table(cls) -> Table:
        return TableImporter.call(File(cls.get_data_file_path()), {
            "index_columns": [0],
            "header": 0,
        })

    @classmethod
    def get_metadata_table(cls) -> Table:
        return MetadataTableImporter.call(File(cls.get_test_data_path("metadata.csv")), {
            "index_columns": [0],
            "header": 0,
        })

    @classmethod
    def get_data_encoding_table(cls) -> Table:
        return EncodingTableImporter.call(File(cls.get_test_data_path("data_encoding.csv")), {
            "original_column": "ocn",
            "original_row": "orn",
            "encoded_column": "ecn",
            "encoded_row": "ern",
        })

    @classmethod
    def get_venn_data_table(cls) -> Table:
        return TableImporter.call(File(cls.get_test_data_path("venn_data.csv")), {
            "delimiter": "tab",
            "header": 0
        })

    @classmethod
    def get_annotated_table(cls) -> Table:
        return AnnotatedTableImporter.call(File(cls.get_test_data_path("annotated_table.csv")), {
            "index_columns": [0],
            "delimiter": ",",
        })
