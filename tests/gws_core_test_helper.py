

import os

from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.impl.table.encoding.annotated_table import AnnotatedTableImporter
from gws_core.impl.table.encoding.encoding_table import EncodingTableImporter
from gws_core.impl.table.encoding.metadata_table import MetadataTableImporter
from gws_core.impl.table.table import Table
from gws_core.impl.table.table_tasks import TableImporter
from gws_core.task.converter.importer_runner import ImporterRunner


class GwsCoreTestHelper():

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
    async def get_iris_table(cls) -> Table:
        return await ImporterRunner(TableImporter, cls.get_iris_file(), {
            "delimiter": ",",
            "header": 0
        }).run()

    @classmethod
    def get_data_file_path(cls) -> str:
        return cls.get_test_data_path("data.csv")

    @classmethod
    async def get_data_table(cls) -> Table:
        return await ImporterRunner(TableImporter, cls.get_data_file_path(), {
            "index_columns": [0],
            "header": 0,
        }).run()

    @classmethod
    async def get_metadata_table(cls) -> Table:
        return await ImporterRunner(MetadataTableImporter, cls.get_test_data_path("metadata.csv"), {
            "index_columns": [0],
            "header": 0,
        }).run()

    @classmethod
    async def get_data_encoding_table(cls) -> Table:
        return await ImporterRunner(EncodingTableImporter, cls.get_test_data_path("data_encoding.csv"), {
            "original_column": "ocn",
            "original_row": "orn",
            "encoded_column": "ecn",
            "encoded_row": "ern",
        }).run()

    @classmethod
    async def get_venn_data_table(cls) -> Table:
        return await ImporterRunner(TableImporter, cls.get_test_data_path("venn_data.csv"), {
            "delimiter": "tab",
            "header": 0
        }).run()

    @classmethod
    async def get_annotated_table(cls) -> Table:
        return await ImporterRunner(AnnotatedTableImporter, cls.get_test_data_path("annotated_table.csv"), {
            "index_columns": [0],
            "delimiter": ",",
        }).run()
