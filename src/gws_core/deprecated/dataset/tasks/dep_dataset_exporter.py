# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from typing import Type

from gws_core.impl.file.file_helper import FileHelper

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param.param_set import ParamSet
from ....core.exception.exceptions import BadRequestException
from ....impl.file.file import File
from ....impl.table.table import Table
from ....impl.table.tasks.table_exporter import TableExporter
from ....task.converter.exporter import exporter_decorator
from ..dep_dataset import Dataset


@exporter_decorator("DatasetExporter", human_name="Dataset exporter", source_type=Dataset,
                    deprecated_since='0.4.4',
                    deprecated_message="Dataset is deprecated. Please use Table",
                    hide=True)
class DatasetExporter(TableExporter):
    config_specs: ConfigSpecs = {**TableExporter.config_specs}

    def export_to_path(self, resource: Table, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        file_name = params.get_value('file_name', type(self)._human_name)
        file_format = FileHelper.clean_extension(params.get_value('file_format', Dataset.DEFAULT_FILE_FORMAT))
        file_path = os.path.join(dest_dir, file_name + '.' + file_format)
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
                "Cannot detect the file type using file extension. Valid file extensions are [xls, xlsx, csv, tsv, txt, tab].")

        return target_type(path=file_path)
