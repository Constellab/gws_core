# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from typing import Type

from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param_set import ParamSet
from ...config.param_spec import BoolParam, IntParam, StrParam
from ...core.exception.exceptions import BadRequestException
from ...impl.file.file import File
from ...impl.table.table import Table
from ...impl.table.tasks.table_exporter import TableExporter
from ...impl.table.tasks.table_importer import TableImporter
from ...task.converter.exporter import exporter_decorator
from ...task.converter.importer import importer_decorator
from .dataset import Dataset


@importer_decorator(unique_name="DatasetImporter", human_name="Dataset importer", target_type=Dataset,
                    supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True, deprecated_since='0.3.3',
                    deprecated_message='Use table importer')
class DatasetImporter(TableImporter):
    config_specs: ConfigSpecs = {
        'file_format': StrParam(default_value=Table.DEFAULT_FILE_FORMAT, allowed_values=Table.ALLOWED_FILE_FORMATS, human_name="File format", short_description="File format"),
        'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, human_name="Delimiter", short_description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, min_value=-1, human_name="Header", short_description="Row to use as the column names. By default the first row is used (i.e. header=0). Set header=-1 to not read column names."),
        "metadata": ParamSet({
            'column': StrParam(default_value=None, optional=True, visibility=StrParam.PUBLIC_VISIBILITY, human_name="Column", short_description="Column to use to tag rows using metadata."),
            'type': StrParam(default_value=Table.CATEGORICAL_TAG_TYPE, optional=True, allowed_values=Table.ALLOWED_TAG_TYPES, visibility=StrParam.PUBLIC_VISIBILITY, human_name="Type", short_description="Types of metadata"),
            'keep_in_table': BoolParam(default_value=True, optional=True, visibility=BoolParam.PUBLIC_VISIBILITY, human_name="Keep in table", short_description="Set True to keep metadata in table; False otherwise"),
            'is_target': BoolParam(default_value=True, optional=True, visibility=BoolParam.PUBLIC_VISIBILITY, human_name="Is target", short_description="Set True to use the column as target; False otherwise"),
        }, optional=True, visibility=ParamSet.PUBLIC_VISIBILITY, human_name="Metadata columns", short_description="Columns data to use to tag rows of the table"),
        'index_column': IntParam(default_value=-1, min_value=-1, optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Index column", short_description="Column to use as the row names. By default no index is used (i.e. index_column=-1)."),
        'decimal': StrParam(default_value=".", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Decimal character", short_description="Character to recognize as decimal point (e.g. use ‘,’ for European/French data)."),
        'nrows': IntParam(default_value=None, optional=True, min_value=0, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Nb. rows", short_description="Number of rows to import. Useful to read piece of data."),
        'comment': StrParam(default_value="#", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Comment character", short_description="Character used to comment lines."),
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Dataset]) -> Dataset:
        dataset: Dataset = await super().import_from_path(file, params, target_type=target_type)

        # set targets names if exist
        targets = []
        metadata_param_set = params.get_value('metadata', [])
        if metadata_param_set:
            for metadata in metadata_param_set:
                colname = metadata.get("column")
                if metadata.get("is_target"):
                    targets.append(colname)
        if targets:
            dataset = target_type(data=dataset.get_data(), target_names=targets)

        return dataset


@exporter_decorator("DatasetExporter", human_name="Dataset exporter", source_type=Dataset, hide=True,
                    deprecated_since='0.3.3', deprecated_message='Use table exporter')
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
