# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Literal

from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.table.table import Table
from gws_core.impl.table.view.table_view import TableView
from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_runner import ViewRunner
from gws_core.resource.view.view_types import CallViewResult

# List of chart callable on a Table
TableChart = Literal['line-plot-2d', 'scatter-plot-2d', 'vulcano-plot',
                     'bar-plot', 'stack-bar-plot', 'histogram',
                     'box-plot', 'heatmap', 'venn-diagram']


class ResourceTableService:
    """Service to manage Table resources
    """

    @classmethod
    def call_table_chart(cls, resource_id: str, table_view_name: str,
                         table_config_values: ConfigParamsDict,
                         chart_type: TableChart,
                         chart_config_values: ConfigParamsDict) -> CallViewResult:
        """Method to call a chart on a table from the table view
        """
        resource_model: ResourceModel = ResourceService.get_resource_by_id(resource_id)
        resource: Resource = resource_model.get_resource()

        view_name = cls._get_table_view_method_name(chart_type)

        # if the resource is a table, call directly the view on it
        if isinstance(resource, Table):
            # call the view and ignore table_config_values as the resource is the Table
            return ResourceService.call_view_on_resource_model(
                resource_model=resource_model, view_name=view_name, config_values=chart_config_values,
                save_view_config=True)

        # otherwise, retrieve the table form the TableView
        table: Table = cls._get_table(resource, table_view_name, table_config_values)

        view_runner: ViewRunner = ViewRunner(table, view_name, chart_config_values)
        view_runner.generate_view()

        return {
            # call the view to dict
            "view": view_runner.call_view_to_dict(),
            "resource_id": resource_model.id,
            "view_config": None
        }

    @classmethod
    def _get_table(cls, resource: Resource, table_view_name: str,
                   table_config_values: ConfigParamsDict) -> Table:
        """Method to retrieve the Table object from the view of a resource
        """

        # Get the table view
        view_runner: ViewRunner = ViewRunner(resource, table_view_name, table_config_values)
        view = view_runner.generate_view()

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
        elif chart == 'vulcano-plot':
            return Table.view_as_vulcano_plot.__name__
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
