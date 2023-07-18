# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Type

from ....config.config_params import ConfigParams
from ....config.config_types import ConfigSpecs
from ....config.param.param_set import ParamSet
from ....config.param.param_spec import BoolParam, IntParam, StrParam
from ....impl.file.file import File
from ....impl.table.table import Table
from ....impl.table.tasks.table_importer import TableImporter
from ....task.converter.importer import importer_decorator
from ..dep_dataset import Dataset


@importer_decorator(unique_name="DatasetImporter", human_name="Dataset importer", target_type=Dataset,
                    supported_extensions=Table.ALLOWED_FILE_FORMATS,
                    deprecated_since='0.4.4',
                    deprecated_message="Dataset is deprecated. Please use Table",
                    hide=True)
class DatasetImporter(TableImporter):
    config_specs: ConfigSpecs = {
        'file_format': StrParam(default_value=Table.DEFAULT_FILE_FORMAT, allowed_values=Table.ALLOWED_FILE_FORMATS, human_name="File format", short_description="File format"),
        'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, human_name="Delimiter", short_description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, min_value=-1, human_name="Header", short_description="Row to use as the column names. By default the first row is used (i.e. header=0). Set header=-1 to not read column names."),
        "metadata_columns": ParamSet({
            'column': StrParam(default_value=None, optional=True, visibility=StrParam.PUBLIC_VISIBILITY, human_name="Column", short_description="Column to use to tag rows using metadata."),
            'keep_in_table': BoolParam(default_value=True, optional=True, visibility=BoolParam.PUBLIC_VISIBILITY, human_name="Keep in table", short_description="Set True to keep metadata in table; False otherwise"),
            'is_target': BoolParam(default_value=True, optional=True, visibility=BoolParam.PUBLIC_VISIBILITY, human_name="Is target", short_description="Set True to use the column as target; False otherwise"),
        }, optional=True, visibility=ParamSet.PUBLIC_VISIBILITY, human_name="Metadata and target columns", short_description="Columns data to use to tag rows of the dataset and also as targets"),
        'index_column': IntParam(default_value=-1, min_value=-1, optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Index column", short_description="Column to use as the row names. By default no index is used (i.e. index_column=-1)."),
        'decimal': StrParam(default_value=".", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Decimal character", short_description="Character to recognize as decimal point (e.g. use ‘,’ for European/French data)."),
        'nrows': IntParam(default_value=None, optional=True, min_value=0, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Nb. rows", short_description="Number of rows to import. Useful to read piece of data."),
        'comment': StrParam(default_value="#", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Comment character", short_description="Character used to comment lines."),
    }

    def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Dataset]) -> Dataset:
        dataset: Dataset = super().import_from_path(file, params, target_type=target_type)

        # set targets names if exist
        targets = []
        metadata_param_set = params.get_value('metadata_columns', [])
        if metadata_param_set:
            for metadata in metadata_param_set:
                colname = metadata.get("column")
                if metadata.get("is_target"):
                    targets.append(colname)

        if targets:
            dataset.set_target_names(target_names=targets)

        return dataset
