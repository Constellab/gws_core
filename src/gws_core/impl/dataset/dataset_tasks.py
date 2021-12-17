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
from ...core.exception.exceptions import BadRequestException
from ...impl.file.file import File
from ...task.converter.exporter import exporter_decorator
from ...task.converter.importer import importer_decorator
from ..table.table_tasks import TableExporter, TableImporter
from .dataset import Dataset


@importer_decorator(unique_name="DatasetImporter", target_type=Dataset)
class DatasetImporter(TableImporter):
    config_specs: ConfigSpecs = {
        'file_format': StrParam(default_value=".csv", short_description="File format"),
        'delimiter': StrParam(default_value='\t', short_description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(optional=True, default_value=0, short_description="Row number to use as the column names. Use -1 to prevent parsing column names. Only for parsing CSV files"),
        'index_columns': ListParam(optional=True, short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for parsing CSV files"),
        'targets': ListParam(default_value='[]', short_description="List of integers or strings (eg. ['name', 6, '7'])"),
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Dataset]) -> Dataset:
        delimiter = params.get_value("delimiter", '\t')
        header = params.get_value("header", 0)
        index_col = params.get_value("index_columns")
        #file_format = params.get_value("file_format")
        targets = params.get_value("targets", [])
        _, file_extension = os.path.splitext(file.path)

        if file_extension in [".xls", ".xlsx"]:
            df = pandas.read_excel(file.path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"]:
            df = pandas.read_table(
                file.path,
                sep=delimiter,
                header=(None if header < 0 else header),
                index_col=index_col
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

        if not targets:
            ds = target_type(features=df)
        else:
            try:
                t_df = df.loc[:, targets]
            except Exception as err:
                raise BadRequestException(
                    f"The targets {targets} are no found in column names. Please check targets names or set parameter 'header' to read column names.") from err
            df.drop(columns=targets, inplace=True)
            ds = target_type(features=df, targets=t_df)
        return ds


@exporter_decorator("DatasetExporter", source_type=Dataset)
class DatasetExporter(TableExporter):
    config_specs: ConfigSpecs = {
        'file_name': StrParam(default_value="file.csv", short_description="File name"),
        'file_format': StrParam(default_value=".csv", short_description="File format"),
        'delimiter': StrParam(default_value="\t", short_description="Delimiter character. Only for parsing CSV files"),
        'write_header': BoolParam(optional=True, short_description="True to write column names (header), False otherwise"),
        'write_index': BoolParam(optional=True, short_description="True to write row names (index), Fasle otherwise"),
    }

    async def export_to_path(self, resource: Dataset, dest_dir: str, params: ConfigParams) -> File:
        file_name = params.get_value("file_name", "file.csv")

        file_path = os.path.join(dest_dir, file_name)
        file_extension = Path(file_path).suffix or params.get_value("file_format", ".csv")
        if file_extension in [".xls", ".xlsx"] or file_extension in [".xls", ".xlsx"]:
            table = resource.get_full_data()
            table.to_excel(file_path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"] or file_extension in [".csv", ".tsv", ".txt", ".tab"]:
            table = resource.get_full_data()
            table.to_csv(
                file_path,
                sep=params.get_value("delimiter", "\t"),
                header=params.get_value("write_header", True),
                index=params.get_value("write_index", True)
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")
