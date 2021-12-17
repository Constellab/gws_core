# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from pathlib import Path
from typing import Type

import pandas

from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...impl.file.file import File
from ...impl.table.table_helper import TableHelper
from ...task.converter.exporter import ResourceExporter, exporter_decorator
from ...task.converter.importer import ResourceImporter, importer_decorator
from .table import Table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="TableImporter", resource_type=Table)
class TableImporter(ResourceImporter):
    input_specs = {'file': File}

    config_specs: ConfigSpecs = {
        'file_format': StrParam(default_value=Table.DEFAULT_FILE_FORMAT, short_description="File format"),
        'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, short_description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, short_description="Row number to use as the column names. Use None to prevent parsing column names. Only for CSV files"),
        'index_columns': ListParam(optional=True, short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for CSV files"),
    }

    async def import_from_path(self, file: File, params: ConfigParams, destination_type: Type[Table]) -> Table:
        file_format: str = params.get_value('file_format', ".csv")
        sep = params.get_value('delimiter', "tab")
        if sep == "tab":
            sep = "\t"
        elif sep == "space":
            sep = " "
        elif sep == "auto":
            sep = TableHelper.detect_csv_delimiter(file.read(size=10000))

        if file.extension in [".xls", ".xlsx"] or file_format in [".xls", ".xlsx"]:
            df = pandas.read_excel(file.path)
        elif file.extension in [".csv", ".tsv", ".txt", ".tab"] or file_format in [".csv", ".tsv", ".txt", ".tab"]:
            df = pandas.read_table(
                file.path,
                sep=sep,
                header=params.get_value('header', 0),
                index_col=params.get_value('index_columns')
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

        return destination_type(data=df)

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator(unique_name="TableExporter", resource_type=Table)
class TableExporter(ResourceExporter):

    output_specs = {"file": File}

    config_specs: ConfigSpecs = {
        'file_name': StrParam(default_value='file.csv', short_description="Destination file name in the store"),
        'file_format': StrParam(default_value=Table.DEFAULT_FILE_FORMAT, short_description="File format"),
        'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, short_description="Delimiter character. Only for CSV files"),
        'write_header': BoolParam(default_value=True, short_description="True to write column names (header), False otherwise"),
        'write_index': BoolParam(default_value=True, short_description="True to write row names (index), False otherwise"),
    }

    async def export_to_path(self, resource: Table, dest_dir: str, params: ConfigParams) -> File:
        file_path = os.path.join(dest_dir, params.get_value('file_name', 'file.csv'))

        file_format: str = params.get_value('file_format', ".csv")
        sep = params.get_value('delimiter', "tab")
        if sep == "tab":
            sep = "\t"
        elif sep == "space":
            sep = " "

        file_extension = Path(file_path).suffix
        if file_extension in [".xls", ".xlsx"] or file_format in [".xls", ".xlsx"]:
            resource._data.to_excel(file_path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"] or file_format in [".csv", ".tsv", ".txt", ".tab"]:
            resource._data.to_csv(
                file_path,
                sep=sep,
                header=params.get_value('write_header', True),
                index=params.get_value('write_index', True)
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

        return File(file_path)
