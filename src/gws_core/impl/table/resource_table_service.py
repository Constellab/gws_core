# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from importlib.resources import Resource
from typing import Any, Dict, List, Literal

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.table.table import Table
from gws_core.impl.table.view.table_view import TableView
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view_helper import ViewHelper
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
        resource_model: ResourceModel = ResourceService.get_resource_by_id(resource_id)
        resource: Resource = resource_model.get_resource()

        view_name = cls._get_table_view_method_name(chart_type)

        # if the resource is a table, call directly the view on it
        if isinstance(resource, Table):
            # call the view and ignore table_config_values as the resource is the Table
            return await ResourceService.call_view_on_resource_model(
                resource_model=resource_model, view_name=view_name, config_values=chart_config_values,
                transformers=table_transformers, save_view_config=True)

        # otherwise, retrieve the table form the TableView
        table: Table = await cls._get_table(resource_id, table_view_name, table_config_values, table_transformers)

        view = await ResourceService.get_view_on_resource(resource, view_name, chart_config_values, [])

        # set title, and technical info if they are not defined in the view
        view = ResourceService.set_default_info_in_view(view, resource_model)

        # call the view to dict
        return ViewHelper.call_view_to_dict(view, chart_config_values, type(table), view_name)

    @classmethod
    async def _get_table(cls, resource: Resource, table_view_name: str,
                         table_config_values: Dict[str, Any],
                         table_transformers: List[TransformerDict]) -> Table:
        """Method to retrieve the Table object from the view of a resource
        """

        # Get the table view
        view: TableView = await ResourceService.get_view_on_resource(
            resource=resource, view_name=table_view_name, config_values=table_config_values,
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
