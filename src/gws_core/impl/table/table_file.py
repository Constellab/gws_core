# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from ...config.config_types import ConfigParams
from ...resource.view_decorator import view
from ..file.file import File
from ..file.importable_resource_decorator import importable_resource_decorator
from .table import Table
from .table_tasks import TableImporter
from .view.table_view import TableView


@importable_resource_decorator("TableFile", resource_importer=TableImporter)
class TableFile(File):
    """Specific file to .csv and .tsv files. This file contains the sames view as the Table resource.

    :param File: [description]
    :type File: [type]
    :return: [description]
    :rtype: [type]
    """

    supported_extensions: List[str] = ['xlsx', 'xls', 'csv', 'tsv']

    @view(view_type=TableView, human_name='Preview', short_description='Preview the table', default_view=True,
          specs=TableImporter.config_specs)
    def preview_as_table(self, params: ConfigParams) -> TableView:
        """
        View as table
        """
        table: Table = TableImporter.call(self, params)
        return table.view_as_table(ConfigParams())
