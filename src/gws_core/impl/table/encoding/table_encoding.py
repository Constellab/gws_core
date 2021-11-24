# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas
from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ....core.exception.exceptions import BadRequestException
from ....impl.file.file import File
from ....resource.r_field import StrRField
from ....resource.resource import Resource
from ....resource.resource_decorator import resource_decorator
from ....resource.view_decorator import view
from ....task.exporter import export_to_path, exporter_decorator
from ....task.importer import import_from_path, importer_decorator
from ..table import Table
from ..table_tasks import TableExporter, TableImporter

# ####################################################################
#
# Encoding class
#
# ####################################################################

ORIGINAL_COLUMN_NAME = "original_row_name"
COLUMN_ORIGINAL_COLUMN_NAME = "original_column_name"
ENCODED_ROW_NAME = "encoded_row_name"
ENCODED_COLUMN_NAME = "encoded_column_name"


@resource_decorator("TableEncoding",
                    human_name="TableEncoding",
                    short_description="Encoding table")
class TableEncoding(Table):
    """
    Represents an encoding table

    For example:

    ```
    ---------------------------------------------------------------------------------------
    original_rowname    | encoded_row_name  |  original_column_name | encoded_column_name
    ---------------------------------------------------------------------------------------
    r-name-1            | r-code-1          |  c-name-1             | c-code-1
    r-name-2            | r-code-2          |  c-name-2             | c-code-2
                        |                   |  c-name-3             | c-code-3
    ---------------------------------------------------------------------------------------
    ```
    """

    ORIGINAL_COLUMN_NAME = ORIGINAL_COLUMN_NAME
    ORIGINAL_ROW_NAME = ORIGINAL_COLUMN_NAME
    ENCODED_ROW_NAME = ENCODED_ROW_NAME
    ENCODED_COLUMN_NAME = ENCODED_COLUMN_NAME

    original_column_name: str = StrRField(default_value=ORIGINAL_COLUMN_NAME)
    original_row_name: str = StrRField(default_value=ORIGINAL_ROW_NAME)
    encoded_column_name: str = StrRField(default_value=ENCODED_ROW_NAME)
    encoded_row_name: str = StrRField(default_value=ENCODED_COLUMN_NAME)

    # -- E --

    # -- G --

    def get_original_column_name(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.original_column_name, rtype)

    def get_original_row_name(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.original_row_name, rtype)

    def get_encoded_row_name(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.encoded_row_name, rtype)

    def get_encoded_column_name(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.encoded_column_name, rtype)

    # -- I --

    @classmethod
    @import_from_path(
        specs={**TableImporter.config_specs,
               'original_column_name': StrParam(default_value=ORIGINAL_COLUMN_NAME, short_description="The original column name"),
               'original_row_name': StrParam(default_value=ORIGINAL_ROW_NAME, short_description="The original row name"),
               'encoded_column_name': StrParam(default_value=ENCODED_COLUMN_NAME, short_description="The encoded column name"),
               'encoded_row_name': StrParam(default_value=ENCODED_ROW_NAME, short_description="The encoded row name"),
               })
    def import_from_path(cls, file: File, params: ConfigParams) -> 'TableEncoding':
        """
        Import from a repository

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed TableEncoding data
        :rtype: TableEncoding
        """

        csv_table = super().import_from_path(file, params)
        original_column_name = params.get_value("original_column_name", cls.ORIGINAL_COLUMN_NAME)
        original_row_name = params.get_value("original_row_name", cls.ORIGINAL_ROW_NAME)
        encoded_column_name = params.get_value("encoded_column_name", cls.ENCODED_COLUMN_NAME)
        encoded_row_name = params.get_value("encoded_row_name", cls.ENCODED_ROW_NAME)

        if not csv_table.column_exists(original_column_name) and not csv_table.column_exists(original_row_name):
            raise BadRequestException(
                f"Cannot import Table. No original column or row name is not found (no columns with name '{original_column_name}' or '{original_row_name}')")

        if csv_table.column_exists(original_column_name) and not csv_table.column_exists(encoded_column_name):
            csv_table = TableEncoding(
                data=pandas.concat([csv_table.data, csv_table[:, original_column_name]]),
                column_names=[*csv_table.columns, encoded_column_name],
                row_names=csv_table.index
            )

        if csv_table.column_exists(original_row_name) and not csv_table.column_exists(encoded_row_name):
            csv_table = TableEncoding(
                data=pandas.concat([csv_table.data, csv_table[:, original_row_name]]),
                column_names=[*csv_table.columns, encoded_row_name],
                row_names=csv_table.index
            )

        csv_table.original_column_name = original_column_name
        csv_table.encoded_column_name = encoded_column_name
        csv_table.original_row_name = original_row_name
        csv_table.encoded_row_name = encoded_row_name

        return csv_table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("TableEncodingImporter", resource_type=TableEncoding)
class TableEncodingImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("TableEncodingExporter", resource_type=TableEncoding)
class TableEncodingExporter(TableExporter):
    pass
