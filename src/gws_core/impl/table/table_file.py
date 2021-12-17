# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.config.param_spec import IntParam, ListParam, StrParam

from ...config.config_types import ConfigParams
from ...config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from ..file.file import File
from .table import Table
from .view.table_view import TableView


@resource_decorator("TableFile")
class TableFile(File):
    """Specific file to .csv and .tsv files. This file contains the sames view as the Table resource.

    :param File: [description]
    :type File: [type]
    :return: [description]
    :rtype: [type]
    """

    supported_extensions: List[str] = ['xlsx', 'xls', 'csv', 'tsv']

    @view(view_type=TableView, human_name='Preview', short_description='Preview the table', default_view=True,
          specs={
              'file_format': StrParam(default_value=Table.DEFAULT_FILE_FORMAT, short_description="File format"),
              'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, short_description="Delimiter character. Only for parsing CSV files"),
              'header': IntParam(default_value=0, short_description="Row number to use as the column names. Use None to prevent parsing column names. Only for CSV files"),
              'index_columns': ListParam(optional=True, short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for CSV files"),
          })
    def preview_as_table(self, params: ConfigParams) -> TableView:
        """
        View as table
        """
        from .table_tasks import TableImporter
        table: Table = TableImporter.call(self, params)
        return table.view_as_table(ConfigParams())
