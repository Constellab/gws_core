# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type

import pandas

from ....config.config_params import ConfigParams
from ....config.config_types import ConfigSpecs
from ....config.param.param_spec import StrParam
from ....core.exception.exceptions import BadRequestException
from ....impl.file.file import File
from ....resource.r_field.primitive_r_field import StrRField
from ....resource.resource_decorator import resource_decorator
from ....task.converter.importer import importer_decorator
from ..table import Table
from ..tasks.table_importer import TableImporter

# ####################################################################
#
# Encoding class
#
# ####################################################################

ORIGINAL_ROW = "original_row"
ORIGINAL_COLUMN = "original_column"
ENCODED_ROW = "encoded_row"
ENCODED_COLUMN = "encoded_column"


@resource_decorator("EncodingTable",
                    human_name="EncodingTable",
                    short_description="Table encoding")
class EncodingTable(Table):
    """
    Represents an encoding table

    For example:

    ```
    ---------------------------------------------------------------------------------------
    original_rowname    | encoded_row  |  original_column | encoded_column
    ---------------------------------------------------------------------------------------
    r-name-1            | r-code-1          |  c-name-1             | c-code-1
    r-name-2            | r-code-2          |  c-name-2             | c-code-2
                        |                   |  c-name-3             | c-code-3
    ---------------------------------------------------------------------------------------
    ```
    """

    ORIGINAL_COLUMN = ORIGINAL_COLUMN
    ORIGINAL_ROW = ORIGINAL_COLUMN
    ENCODED_ROW = ENCODED_ROW
    ENCODED_COLUMN = ENCODED_COLUMN

    original_column: str = StrRField(default_value=ORIGINAL_COLUMN)
    original_row: str = StrRField(default_value=ORIGINAL_ROW)
    encoded_column: str = StrRField(default_value=ENCODED_ROW)
    encoded_row: str = StrRField(default_value=ENCODED_COLUMN)

    def get_original_column_data(self) -> list:
        return self.get_column_data(self.original_column)

    def get_original_row_data(self) -> list:
        return self.get_column_data(self.original_row)

    def get_encoded_row_data(self) -> list:
        return self.get_column_data(self.encoded_row)

    def get_encoded_column_data(self) -> list:
        return self.get_column_data(self.encoded_column)

    def select_by_column_indexes(self, positions: List[int]) -> 'EncodingTable':
        raise BadRequestException("Not allowed of EncodingTable")

    def select_by_column_name(self, name_regex: str) -> 'Table':
        raise BadRequestException("Not allowed of EncodingTable")

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("EncodingTableImporter", target_type=EncodingTable, supported_extensions=Table.ALLOWED_FILE_FORMATS)
class EncodingTableImporter(TableImporter):
    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'original_column': StrParam(default_value=ORIGINAL_COLUMN, short_description="The original column name"),
        'original_row': StrParam(default_value=ORIGINAL_ROW, short_description="The original row name"),
        'encoded_column': StrParam(default_value=ENCODED_COLUMN, short_description="The encoded column name"),
        'encoded_row': StrParam(default_value=ENCODED_ROW, short_description="The encoded row name"), }

    def import_from_path(self, file: File, params: ConfigParams, target_type: Type[EncodingTable]) -> EncodingTable:
        csv_table: EncodingTable = super().import_from_path(file, params, target_type)
        original_column = params.get_value("original_column", target_type.ORIGINAL_COLUMN)
        original_row = params.get_value("original_row", target_type.ORIGINAL_ROW)
        encoded_column = params.get_value("encoded_column", target_type.ENCODED_COLUMN)
        encoded_row = params.get_value("encoded_row", target_type.ENCODED_ROW)

        if not csv_table.column_exists(original_column) and not csv_table.column_exists(original_row):
            raise BadRequestException(
                f"Cannot import Table. No original column or row name is not found (no columns with name '{original_column}' or '{original_row}')")

        if csv_table.column_exists(original_column) and not csv_table.column_exists(encoded_column):
            csv_table = EncodingTable(
                data=pandas.concat([csv_table.data, csv_table[:, original_column]]),
                column_names=[*csv_table.columns, encoded_column],
                row_names=csv_table.index
            )

        if csv_table.column_exists(original_row) and not csv_table.column_exists(encoded_row):
            csv_table = EncodingTable(
                data=pandas.concat([csv_table.data, csv_table[:, original_row]]),
                column_names=[*csv_table.columns, encoded_row],
                row_names=csv_table.index
            )

        csv_table.original_column = original_column
        csv_table.encoded_column = encoded_column
        csv_table.original_row = original_row
        csv_table.encoded_row = encoded_row

        return csv_table
