# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict, List, Literal

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.table.table import Table
from gws_core.impl.table.view.table_view import TableView
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view_types import ViewCallResult
from gws_core.task.transformer.transformer_type import TransformerDict

# List of chart callable on a Table
TableChart = Literal['line-plot-2d', 'scatter-plot-2d', 'bar-plot',
                     'stack-bar-plot', 'histogram', 'box-plot', 'heatmap', 'venn-diagram']


class ResourceTableService:
    """Service to manage Table resources
    """

    @classmethod
    async def call_table_chart(cls, resource_id: str, table_view_name: str,
                               table_config_values: Dict[str, Any],
                               table_transformers: List[TransformerDict],
                               chart_type: TableChart,
                               chart_config_values: Dict[str, Any]) -> ViewCallResult:
        """Method to call a chart on a table from the table view
        """
        table: Table = await cls._get_table(resource_id, table_view_name, table_config_values, table_transformers)

        view_name = cls._get_table_view_method_name(chart_type)

        # call the chart view on the table (without transformer, they where used to generate the table)
        return await ResourceService.call_view_on_resource(table, view_name, chart_config_values, [])

    @classmethod
    async def _get_table(cls, resource_id: str, table_view_name: str,
                         table_config_values: Dict[str, Any],
                         table_transformers: List[TransformerDict]) -> Table:
        """Method to retrieve the Table object from the view of a resource
        """

        # Get the table view
        view: TableView = await ResourceService.get_view_on_resource_type(
            resource_model_id=resource_id, view_name=table_view_name, config_values=table_config_values,
            transformers=table_transformers)

        if not isinstance(view, TableView):
            raise BadRequestException('The base view is not a table view')
        return view.get_table()

    @classmethod
    def _get_table_view_method_name(cls, chart: TableChart) -> str:
        """Retrieve the table view method name based on chart type

        :param chart: _description_
        :type chart: TableChart
        :raises BadRequestException: _description_
        :return: _description_
        :rtype: str
        """
        if chart == 'line-plot-2d':
            return Table.view_as_line_plot_2d.__name__
        elif chart == 'scatter-plot-2d':
            return Table.view_as_scatter_plot_2d.__name__
        elif chart == 'bar-plot':
            return Table.view_as_bar_plot.__name__
        elif chart == 'stack-bar-plot':
            return Table.view_as_stacked_bar_plot.__name__
        elif chart == 'histogram':
            return Table.view_as_histogram.__name__
        elif chart == 'box-plot':
            return Table.view_as_box_plot.__name__
        elif chart == 'heatmap':
            return Table.view_as_heatmap.__name__
        elif chart == 'venn-diagram':
            return Table.view_as_venn_diagram.__name__
        else:
            raise BadRequestException(f"Chart {chart} not supported for table")
