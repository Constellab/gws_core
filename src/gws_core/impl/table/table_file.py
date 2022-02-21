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

    NB_ROWS = 150
    supported_extensions: List[str] = ['xlsx', 'xls', 'csv', 'tsv']

    @view(view_type=TableView, human_name='Preview', short_description=f'Preview the table', default_view=True,
          specs={
              'file_format': StrParam(default_value=Table.DEFAULT_FILE_FORMAT, short_description="File format"),
              'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, short_description="Delimiter character. Only for parsing CSV files"),
              'header': IntParam(default_value=0, min_value=0, human_name="Header", short_description="Row number to use as the column names, and the start of the data. By default the first row is used. Use 0 to prevent parsing column names."),
              'index_column': IntParam(default_value=None, min_value=0, optional=True, human_name="Index column", short_description="Column index to use as the row name. By default no column is used."),
              'decimal': StrParam(default_value=".", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Decimal character", short_description="Character to recognize as decimal point (e.g. use ‘,’ for European/French data)."),
              'nrows': IntParam(default_value=NB_ROWS, optional=True, min_value=0, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Nb. rows", short_description="Number of rows to import. Useful to read piece of data."),
              'comment': StrParam(default_value="#", optional=True, visibility=IntParam.PROTECTED_VISIBILITY, human_name="Comment character", short_description="Character used to comment lines."),
          })
    def preview_as_table(self, params: ConfigParams) -> TableView:
        """
        View as table
        """
        from .tasks.table_importer import TableImporter
        table: Table = TableImporter.call(self, params)
        return table.view_as_table(ConfigParams())
