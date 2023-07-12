# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from pandas import DataFrame, read_excel, read_table

from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.logger import Logger
from gws_core.impl.file.file_helper import FileHelper

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param.param_set import ParamSet
from ....config.param.param_spec import BoolParam, IntParam, StrParam
from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....impl.file.file import File
from ....task.converter.importer import ResourceImporter, importer_decorator
from ..helper.dataframe_helper import DataframeHelper
from ..table import Table


@importer_decorator(unique_name="TableImporter", target_type=Table, supported_extensions=Table.ALLOWED_FILE_FORMATS)
class TableImporter(ResourceImporter):
    config_specs: ConfigSpecs = {
        'file_format': StrParam(allowed_values=['auto', *Table.ALLOWED_FILE_FORMATS], default_value='auto', human_name="File format", short_description="File format"),
        'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, human_name="Delimiter", short_description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, min_value=-1, human_name="Header", short_description="Row to use as the column names. By default the first row is used (i.e. header=0). Set header=-1 to not read column names."),
        'format_header_names': BoolParam(default_value=False, optional=True, human_name="Format header names", short_description="If true, the column and row names are formatted to remove special characters and spaces (only '_' are allowed)."),
        'index_column': IntParam(default_value=-1, min_value=-1, optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Index column", short_description="Column to use as the row names. By default no index is used (i.e. index_column=-1)."),
        'decimal': StrParam(default_value=".", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Decimal character", short_description="Character to recognize as decimal point (e.g. use ‘,’ for European/French data)."),
        'nrows': IntParam(default_value=None, optional=True, min_value=0, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Number of rows", short_description="Number of rows to import. Useful to read piece of data."),
        'comment': StrParam(default_value="#", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Comment character", short_description="Character used to comment lines. Set empty to disable comment lines."),
        'encoding': StrParam(default_value="auto", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="File encoding", short_description="Encoding of the file, 'auto' for automatic detection."),
        "metadata_columns": ParamSet({
            'column': StrParam(default_value=None, optional=True, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Column", short_description="Metadata column to use to tag rows"),
            'keep_in_table': BoolParam(default_value=False, optional=True, visibility=BoolParam.PROTECTED_VISIBILITY, human_name="Keep in table", short_description="Set True to keep the column in the final table; False otherwise"),
        }, optional=True, visibility=ParamSet.PROTECTED_VISIBILITY, human_name="Metadata columns", short_description="Columns data to use to tag the rows of the table"),
    }

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[Table]) -> Table:
        Logger.error('NOOOOOOOOOOOOOOOOOOOOOOOOOOO nullll \n deuxieme ligne eeeeeee')
        a = {}
        b = a.super()
        if source.is_empty():
            raise BadRequestException(GWSException.EMPTY_FILE.value, unique_code=GWSException.EMPTY_FILE.name,
                                      detail_args={'filename': source.path})

        file_format: str = self.get_file_format(source, params.get_value('file_format'))

        encoding = params.get('encoding')
        if encoding == 'auto' or encoding is None or len(encoding) == 0:
            encoding = FileHelper.detect_file_encoding(source.path)
            self.log_info_message(f"Detected encoding: {encoding}")

        # the empty string meanse no comment
        comment_char = params.get_value('comment')
        if comment_char == "":
            comment_char = None

        dataframe: DataFrame = None
        # import the dataframe
        if source.extension in Table.ALLOWED_XLS_FILE_FORMATS or file_format in Table.ALLOWED_XLS_FILE_FORMATS:
            dataframe = self._import_excel(source)
        elif source.extension in Table.ALLOWED_TXT_FILE_FORMATS or file_format in Table.ALLOWED_TXT_FILE_FORMATS:
            dataframe = self._import_csv(
                source, params, comment_char, encoding)
        else:
            raise BadRequestException(
                f"Valid file formats are {Table.ALLOWED_FILE_FORMATS}.")

        table: Table = None
        # set metadata and build Table
        metadata_columns = params.get_value('metadata_columns', [])
        if metadata_columns:
            row_tags = []
            meta_cols = []
            keep_in_table = {}
            for metadata in metadata_columns:
                colname = metadata.get("column")
                meta_cols.append(colname)
                keep_in_table[colname] = metadata.get("keep_in_table") or False

            tag_df = dataframe[meta_cols]
            drop_cols = [col for col, keep in keep_in_table.items()
                         if keep is False]
            if drop_cols:
                dataframe.drop(drop_cols, axis=1, inplace=True)
            for idx in dataframe.index:
                tag = {col: tag_df.loc[idx, col] for col in tag_df.columns}
                row_tags.append(tag)

            table = target_type(data=dataframe, format_header_names=params.get(
                'format_header_names', False))
            table.set_all_row_tags(row_tags)
        else:
            table = target_type(data=dataframe, format_header_names=params.get(
                'format_header_names', False))

        table.set_comments(self._read_comments(source, comment_char, encoding))
        return table

    def get_file_format(self, source: File, file_format: str) -> str:
        clean_file_format: str = FileHelper.clean_extension(file_format)

        if clean_file_format == "auto":
            extension = source.extension

            if not extension in Table.ALLOWED_FILE_FORMATS:
                raise Exception(f"File format {extension} not supported.")

            return source.extension

        return clean_file_format

    def _import_excel(self, source: File) -> DataFrame:
        return read_excel(source.path)

    def _import_csv(self, source: File, params: ConfigParams, comment_char: str, encoding: str) -> DataFrame:

        header = params.get_value('header')
        header = (None if header == -1 else header)

        index_column = params.get_value('index_column')
        index_column = (None if index_column == -1 else index_column)

        decimal = params.get_value('decimal')

        nrows = params.get_value('nrows')

        sep = params.get_value('delimiter')
        if sep == "tab":
            sep = "\t"
        elif sep == "space":
            sep = " "
        elif sep == "auto":
            sep = DataframeHelper.detect_csv_delimiter(
                source.read(size=10000))

        return read_table(
            source.path,
            sep=sep,
            header=header,
            index_col=index_column,
            nrows=nrows,
            decimal=decimal,
            comment=comment_char,
            encoding=encoding,
        )

    def _read_comments(self, source: File, comment_char: str, encoding: str) -> str:
        if not source.is_readable():
            return ""

        comments = ""

        if comment_char:
            with open(source.path, 'r', encoding=encoding) as fp:
                for line in fp:
                    if line.startswith(comment_char):
                        comments += line
                    else:
                        break

        return comments
