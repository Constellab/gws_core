# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from pathlib import Path
from typing import Type

import pandas
from gws_core.impl.table.table_file import TableFile

from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...impl.file.file import File
from ...impl.table.table_helper import TableHelper
from ...task.converter.exporter import ResourceExporter, exporter_decorator
from ...task.converter.importer import ResourceImporter, importer_decorator
from .table import Table
from .table_file import TableFile

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="TableImporter", source_type=TableFile, target_type=Table)
class TableImporter(ResourceImporter):
    config_specs: ConfigSpecs = {
        'file_format': StrParam(default_value=Table.DEFAULT_FILE_FORMAT, allowed_values=Table.ALLOWED_FILE_FORMATS, short_description="File format"),
        'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, short_description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, min_value=-1, short_description="Row number to use as the column names. Use -1 to prevent parsing column names. Only for CSV files"),
        'index_columns': ListParam(optional=True, short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for CSV files"),
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Table]) -> Table:
        file_format: str = params.get_value('file_format', Table.DEFAULT_FILE_FORMAT)
        sep = params.get_value('delimiter', Table.DEFAULT_DELIMITER)
        header = params.get_value('header', 0)
        if sep == "tab":
            sep = "\t"
        elif sep == "space":
            sep = " "
        elif sep == "auto":
            sep = TableHelper.detect_csv_delimiter(file.read(size=10000))

        if file.extension in Table.ALLOWED_XLS_FILE_FORMATS or file_format in Table.ALLOWED_XLS_FILE_FORMATS:
            df = pandas.read_excel(file.path)
        elif file.extension in Table.ALLOWED_TXT_FILE_FORMATS or file_format in Table.ALLOWED_TXT_FILE_FORMATS:
            df = pandas.read_table(
                file.path,
                sep=sep,
                header=(None if header < 0 else header),
                index_col=params.get_value('index_columns')
            )
        else:
            raise BadRequestException(
                "Valid file formats are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

        return target_type(data=df)

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator(unique_name="TableExporter", source_type=Table, target_type=TableFile)
class TableExporter(ResourceExporter):
    config_specs: ConfigSpecs = {
        'file_name': StrParam(default_value='file', short_description="File name (without extension)"),
        'file_format': StrParam(default_value=Table.DEFAULT_FILE_FORMAT, allowed_values=Table.ALLOWED_FILE_FORMATS, short_description="File format"),
        'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, short_description="Delimiter character. Only for CSV files"),
        'write_header': BoolParam(default_value=True, short_description="True to write column names (header), False otherwise"),
        'write_index': BoolParam(default_value=True, short_description="True to write row names (index), False otherwise"),
    }

    async def export_to_path(self, resource: Table, dest_dir: str, params: ConfigParams, target_type: Type[TableFile]) -> TableFile:
        file_name = params.get_value('file_name', 'file')
        file_format = params.get_value('file_format', Table.DEFAULT_FILE_FORMAT)
        file_path = os.path.join(dest_dir, file_name+file_format)
        sep = params.get_value('delimiter', Table.DEFAULT_DELIMITER)
        if sep == "tab":
            sep = "\t"
        elif sep == "space":
            sep = " "
        elif sep == "auto":
            sep = ","

        if file_format in Table.ALLOWED_XLS_FILE_FORMATS:
            resource.get_data().to_excel(file_path)
        elif file_format in Table.ALLOWED_TXT_FILE_FORMATS:
            resource.get_data().to_csv(
                file_path,
                sep=sep,
                header=params.get_value('write_header', True),
                index=params.get_value('write_index', True)
            )
        else:
            raise BadRequestException(
                f"Valid file formats are {Table.ALLOWED_FILE_FORMATS}.")

        return target_type(path=file_path)
