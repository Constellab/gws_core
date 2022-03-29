# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

import pandas
from gws_core.core.exception.gws_exceptions import GWSException

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import BoolParam, IntParam, ParamSet, StrParam
from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....impl.file.file import File
from ....impl.table.table_helper import TableHelper
from ....task.converter.importer import ResourceImporter, importer_decorator
from ..table import Table


@importer_decorator(unique_name="TableImporter", target_type=Table, supported_extensions=Table.ALLOWED_FILE_FORMATS)
class TableImporter(ResourceImporter):
    config_specs: ConfigSpecs = {
        'file_format': StrParam(default_value=Table.DEFAULT_FILE_FORMAT, allowed_values=Table.ALLOWED_FILE_FORMATS, human_name="File format", short_description="File format"),
        'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, human_name="Delimiter", short_description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, min_value=-1, human_name="Header", short_description="Row to use as the column names. By default the first row is used (i.e. header=0). Set header=-1 to not read column names."),
        "metadata_columns": ParamSet({
            'column': StrParam(default_value=None, optional=True, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Column", short_description="Column to use to tag rows using metadata."),
            'type': StrParam(default_value=Table.CATEGORICAL_TAG_TYPE, optional=True, allowed_values=Table.ALLOWED_TAG_TYPES, visibility=StrParam.PUBLIC_VISIBILITY, human_name="Type", short_description="Types of metadata"),
            'keep_in_table': BoolParam(default_value=True, optional=True, visibility=BoolParam.PROTECTED_VISIBILITY, human_name="Keep in table", short_description="Set True to keep metadata in table; False otherwise"),
        }, optional=True, visibility=ParamSet.PROTECTED_VISIBILITY, human_name="Metadata columns", short_description="Columns data to use to tag rows of the table"),
        'index_column': IntParam(default_value=-1, min_value=-1, optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Index column", short_description="Column to use as the row names. By default no index is used (i.e. index_column=-1)."),
        'decimal': StrParam(default_value=".", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Decimal character", short_description="Character to recognize as decimal point (e.g. use ‘,’ for European/French data)."),
        'nrows': IntParam(default_value=None, optional=True, min_value=0, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Number of rows", short_description="Number of rows to import. Useful to read piece of data."),
        'comment': StrParam(default_value="#", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Comment character", short_description="Character used to comment lines."),
    }

    async def import_from_path(self, source: File, params: ConfigParams, target_type: Type[Table]) -> Table:
        if source.is_empty():
            raise BadRequestException(GWSException.EMPTY_FILE.value, unique_code=GWSException.EMPTY_FILE.name)

        file_format: str = params.get_value('file_format', Table.DEFAULT_FILE_FORMAT)
        sep = params.get_value('delimiter', Table.DEFAULT_DELIMITER)
        header = params.get_value('header', 0)
        index_column = params.get_value('index_column', -1)
        metadata_columns = params.get_value('metadata_columns', [])
        comment_char = params.get_value('comment', "#")
        nrows = params.get_value('nrows')

        header = (None if header == -1 else header)
        index_column = (None if index_column == -1 else index_column)

        if sep == "tab":
            sep = "\t"
        elif sep == "space":
            sep = " "
        elif sep == "auto":
            sep = TableHelper.detect_csv_delimiter(source.read(size=10000))

        if source.extension in Table.ALLOWED_XLS_FILE_FORMATS or file_format in Table.ALLOWED_XLS_FILE_FORMATS:
            df = pandas.read_excel(source.path)
        elif source.extension in Table.ALLOWED_TXT_FILE_FORMATS or file_format in Table.ALLOWED_TXT_FILE_FORMATS:
            df = pandas.read_table(
                source.path,
                sep=sep,
                header=header,
                index_col=index_column,
                nrows=nrows,
                comment=comment_char
            )
        else:
            raise BadRequestException(
                f"Valid file formats are {Table.ALLOWED_FILE_FORMATS}.")

        df.columns = df.columns.map(str)

        # set metadata
        if metadata_columns:
            row_tags = []
            meta_cols = []
            meta_types = {}
            keep_in_table = {}
            for metadata in metadata_columns:
                colname = metadata.get("column")
                meta_cols.append(colname)
                meta_types[colname] = metadata.get("type", Table.CATEGORICAL_TAG_TYPE)
                keep_in_table[colname] = metadata.get("keep_in_table", True)

            tag_df = df[meta_cols]
            drop_cols = [col for col, keep in keep_in_table.items() if keep == False]
            if drop_cols:
                df.drop(drop_cols, axis=1, inplace=False)
            for idx in df.index:
                tag = {col: tag_df.loc[idx, col] for col in tag_df.columns}
                row_tags.append(tag)

            table = target_type(data=df)
            table.set_row_tags(row_tags)
            table.set_row_tag_types(meta_types)
        else:
            table = target_type(data=df)

        # read comments
        comments = ""
        with open(source.path, 'r', encoding="utf-8") as fp:
            for line in fp:
                if line.startswith(comment_char):
                    comments += line
                else:
                    break

        table.set_comments(comments)
        return table
