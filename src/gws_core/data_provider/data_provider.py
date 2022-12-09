

import os

from gws_core import File, Settings, Table, TableImporter


class DataProvider():

    @classmethod
    def _get_test_data_dir(cls) -> str:
        return Settings.get_instance().get_variable("gws_core:testdata_dir")

    @classmethod
    def get_test_data_path(cls, path: str) -> str:
        return os.path.join(cls._get_test_data_dir(), path)

    @classmethod
    def get_test_data_file(cls, path: str) -> File:
        return File(cls.get_test_data_path(path))

    @classmethod
    def get_iris_file(cls) -> File:
        return File(cls.get_test_data_path('iris.csv'))

    @classmethod
    def get_no_head_iris_file(cls) -> File:
        return File(cls.get_test_data_path('iris_no_head.csv'))

    @classmethod
    def get_iris_table(cls, keep_variety: bool = True) -> Table:
        return TableImporter.call(cls.get_iris_file(), {
            "delimiter": ",",
            "header": 0,
            "metadata_columns": [{
                "column": "variety",
                "keep_in_table": keep_variety,
            }]
        })
