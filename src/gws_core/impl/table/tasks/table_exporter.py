# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import Type

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import BoolParam, StrParam
from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....task.converter.exporter import ResourceExporter, exporter_decorator
from ..table import Table
from ..table_file import TableFile


@exporter_decorator(unique_name="TableExporter", source_type=Table, target_type=TableFile)
class TableExporter(ResourceExporter):
    config_specs: ConfigSpecs = {
        'file_name': StrParam(optional=True, short_description="File name (without extension)"),
        'file_format': StrParam(optional=True, default_value=Table.DEFAULT_FILE_FORMAT, allowed_values=Table.ALLOWED_FILE_FORMATS, short_description="File format"),
        'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, short_description="Delimiter character. Only for CSV files"),
        'write_header': BoolParam(default_value=True, short_description="True to write column names (header), False otherwise"),
        'write_index': BoolParam(default_value=True, short_description="True to write row names (index), False otherwise"),
    }

    async def export_to_path(self, source: Table, dest_dir: str, params: ConfigParams, target_type: Type[TableFile]) -> TableFile:
        file_name = params.get_value('file_name', type(self)._human_name)
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
            source.get_data().to_excel(file_path)
        elif file_format in Table.ALLOWED_TXT_FILE_FORMATS:
            source.get_data().to_csv(
                file_path,
                sep=sep,
                header=params.get_value('write_header', True),
                index=params.get_value('write_index', True)
            )
        else:
            raise BadRequestException(
                f"Valid file formats are {Table.ALLOWED_FILE_FORMATS}.")

        return target_type(path=file_path)
