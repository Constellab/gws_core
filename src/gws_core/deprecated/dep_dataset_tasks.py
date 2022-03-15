# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from typing import Type

import pandas
from gws_core import ListParam

from ..config.config_types import ConfigParams, ConfigSpecs
from ..core.exception.exceptions import BadRequestException
from ..impl.file.file import File
from ..impl.table.table import Table
from ..impl.table.table_helper import TableHelper
from ..task.converter.exporter import exporter_decorator
from ..task.converter.importer import importer_decorator
from ..impl.table.tasks.table_exporter import TableExporter
from ..impl.table.tasks.table_importer import TableImporter
from .dep_dataset import Dataset


@importer_decorator(unique_name="DatasetImporter", target_type=Dataset, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True, deprecated_since='0.3.3', deprecated_message='Use table importer')
class DatasetImporter(TableImporter):
    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'targets': ListParam(default_value='[]', short_description="Name of the columns to user as targets"),
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Dataset]) -> Dataset:
        header = params.get_value("header", 0)
        index_column = params.get_value("index_column", -1)
        targets = params.get_value("targets", [])

        header = (None if header == -1 else header)
        index_column = (None if index_column == -1 else index_column)
        dataset = await super().import_from_path(file, params, target_type=target_type)

        # file_format: str = params.get_value('file_format', Dataset.DEFAULT_FILE_FORMAT)
        # sep = params.get_value('delimiter', Dataset.DEFAULT_DELIMITER)
        # if sep == "tab":
        #     sep = "\t"
        # elif sep == "space":
        #     sep = " "
        # elif sep == "auto":
        #     sep = TableHelper.detect_csv_delimiter(file.read(size=10000))

        # if file_format in Dataset.ALLOWED_XLS_FILE_FORMATS:
        #     df = pandas.read_excel(file.path)
        # elif file_format in Dataset.ALLOWED_TXT_FILE_FORMATS:
        #     df = pandas.read_table(
        #         file.path,
        #         sep=sep,
        #         header=header,
        #         index_col=index_column
        #     )
        # else:
        #     raise BadRequestException(
        #         f"Cannot detect the file type using file extension. Valid file extensions are {Dataset.ALLOWED_FILE_FORMATS}.")
        
        dataset = target_type(data=dataset.get_data(), target_names=targets)
        
        return dataset


@exporter_decorator("DatasetExporter", source_type=Dataset, hide=True, deprecated_since='0.3.3', deprecated_message='Use table exporter')
class DatasetExporter(TableExporter):
    config_specs: ConfigSpecs = {**TableExporter.config_specs}

    async def export_to_path(self, resource: Table, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        file_name = params.get_value('file_name', type(self)._human_name)
        file_format = params.get_value('file_format', Dataset.DEFAULT_FILE_FORMAT)
        file_path = os.path.join(dest_dir, file_name+file_format)

        sep = params.get_value('delimiter', Dataset.DEFAULT_DELIMITER)
        if sep == "tab":
            sep = "\t"
        elif sep == "space":
            sep = " "
        elif sep == "auto":
            sep = ","

        if file_format in Dataset.ALLOWED_XLS_FILE_FORMATS:
            table = resource.get_full_data()
            table.to_excel(file_path)
        elif file_format in Dataset.ALLOWED_TXT_FILE_FORMATS:
            table = resource.get_full_data()
            table.to_csv(
                file_path,
                sep=sep,
                header=params.get_value("write_header", True),
                index=params.get_value("write_index", True)
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

        return target_type(path=file_path)
