# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from ...config.config_types import ConfigParams
from ...resource.multi_views import MultiViews
from ...resource.view_decorator import view
from ..file.file import File
from ..file.file_helper import FileHelper
from ..file.importable_resource_decorator import importable_resource_decorator
from .table import Table
from .table_tasks import TableImporter
from .view.barplot_view import TableBarPlotView
from .view.boxplot_view import TableBoxPlotView
from .view.heatmap_view import HeatmapView
from .view.histogram_view import TableHistogramView
from .view.lineplot_2d_view import TableLinePlot2DView
from .view.scatterplot_2d_view import TableScatterPlot2DView
from .view.stacked_barplot_view import TableStackedBarPlotView
from .view.table_view import TableView
from .view.venn_diagram_view import TableVennDiagramView


@importable_resource_decorator("TableFile", resource_importer=TableImporter)
class TableFile(File):
    """Specific file to .csv and .tsv files. This file contains the sames view as the Table resource.

    :param File: [description]
    :type File: [type]
    :return: [description]
    :rtype: [type]
    """

    supported_extensions: List[str] = ['xlsx', 'xls', 'csv', 'tsv']

    @view(view_type=TableView, human_name='Tabular', short_description='View as a table', default_view=True)
    def view_as_table(self, params: ConfigParams) -> TableView:
        """
        View as table
        """

        return self._get_table_resource().view_as_table(params)

    @view(view_type=TableLinePlot2DView, human_name='LinePlot2D', short_description='View columns as 2D-line plots', specs={})
    def view_as_line_plot_2d(self, params: ConfigParams) -> TableLinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return self._get_table_resource().view_as_line_plot_2d(params)

    # @view(view_type=TableLinePlot3DView, human_name='LinePlot3D', short_description='View columns as 3D-line plots', specs={})
    # def view_as_line_plot_3d(self, params: ConfigParams) -> TableLinePlot3DView:
    #     """
    #     View columns as 3D-line plots
    #     """

    #     return self._get_table_resource().view_as_line_plot_3d(params)

    # @view(view_type=TableScatterPlot3DView, human_name='ScatterPlot3D', short_description='View columns as 3D-scatter plots',
    #       specs={})
    # def view_as_scatter_plot_3d(self, params: ConfigParams) -> TableScatterPlot3DView:
    #     """
    #     View columns as 3D-scatter plots
    #     """

    #     return self._get_table_resource().view_as_scatter_plot_3d(params)

    @view(view_type=TableScatterPlot2DView, human_name='ScatterPlot2D',
          short_description='View columns as 2D-scatter plots', specs={})
    def view_as_scatter_plot_2d(self, params: ConfigParams) -> TableScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return self._get_table_resource().view_as_scatter_plot_2d(params)

    @view(view_type=TableHistogramView, human_name='Histogram', short_description='View columns as 2D-line plots',
          specs={})
    def view_as_histogram(self, params: ConfigParams) -> TableHistogramView:
        """
        View columns as 2D-line plots
        """

        return self._get_table_resource().view_as_histogram(params)

    @view(view_type=TableBoxPlotView, human_name='BoxPlot', short_description='View columns as box plots', specs={})
    def view_as_box_plot(self, params: ConfigParams) -> TableBoxPlotView:
        """
        View one or several columns as box plots
        """

        return self._get_table_resource().view_as_box_plot(params)

    @view(view_type=TableBarPlotView, human_name='Bar plot', short_description='View columns as 2D-bar plots', specs={})
    def view_as_bar_plot(self, params: ConfigParams) -> TableBarPlotView:
        """
        View one or several columns as 2D-bar plots
        """

        return self._get_table_resource().view_as_bar_plot(params)

    @view(view_type=TableStackedBarPlotView, human_name='Stacked bar plot',
          short_description='View columns as 2D-stacked bar plots', specs={})
    def view_as_stacked_bar_plot(self, params: ConfigParams) -> TableStackedBarPlotView:
        """
        View one or several columns as 2D-stacked bar plots
        """

        return self._get_table_resource().view_as_stacked_bar_plot(params)

    @view(view_type=HeatmapView, human_name='Heatmap', short_description='View table as heatmap', specs={})
    def view_as_heatmap(self, params: ConfigParams) -> HeatmapView:
        """
        View the table as heatmap
        """

        return self._get_table_resource().view_as_heatmap(params)

    @view(view_type=TableVennDiagramView, human_name='Venn', short_description='Venn diagram', specs={})
    def view_as_venn_diagram(self, params: ConfigParams) -> TableVennDiagramView:
        """
        View the table as heatmap
        """

        table: Table = self._get_table_resource()
        return TableVennDiagramView(table.get_data())

    @view(view_type=MultiViews, human_name='Multi view', short_description='Multi view', specs={})
    def view_as_multi_views(self, params: ConfigParams) -> MultiViews:
        """
        View one or several columns as box plots
        """

        multi_views: MultiViews = MultiViews(nb_of_columns=4)
        multi_views.add_view(self.view_as_scatter_plot_2d(params), {
                             "x_column_name": "one", "y_column_names": ["two", "three"]}, 3, 1)
        multi_views.add_view(self.view_as_line_plot_2d(params), {
                             "x_column_name": "one", "y_column_names": ["two", "three"]}, 1, 3)
        multi_views.add_view(self.view_as_table(params), {}, 2, 2)
        # multi_views.add_view(self.view_as_table().to_dict(), 2, 2)
        multi_views.add_view(self.view_as_json(params), {}, 1, 2)
        multi_views.add_empty_block(2, 2)

        return multi_views

    def _get_table_resource(self) -> Table:
        # guess the delimiter
        max_nb_chars = 10000
        delimiter = FileHelper.detect_csv_delimiter(self.read(size=max_nb_chars))
        return Table.import_from_path(self, ConfigParams(delimiter=delimiter, header=0))
