import os
from typing import cast

from gws_core import File, Settings, Table, TableImporter
from gws_core.impl.file.file_helper import FileHelper


class DataProvider:
    @classmethod
    def _get_test_data_dir(cls) -> str:
        return Settings.get_instance().get_and_check_variable("gws_core", "testdata_dir")

    @classmethod
    def get_test_data_path(cls, path: str) -> str:
        return os.path.join(cls._get_test_data_dir(), path)

    @classmethod
    def get_iris_file(cls) -> File:
        return File(cls.get_test_data_path("iris.csv"))

    @classmethod
    def get_new_empty_file(cls) -> File:
        temp_dir = Settings.make_temp_dir()
        file_path = FileHelper.create_empty_file_if_not_exist(os.path.join(temp_dir, "empty.txt"))
        return File(file_path)

    @classmethod
    def get_iris_table(cls, keep_variety: bool = True) -> Table:
        return cast(
            Table,
            TableImporter.call(
                cls.get_iris_file(),
                {
                    "delimiter": ",",
                    "header": 0,
                    "metadata_columns": [
                        {
                            "column": "variety",
                            "keep_in_table": keep_variety,
                        }
                    ],
                },
            ),
        )
