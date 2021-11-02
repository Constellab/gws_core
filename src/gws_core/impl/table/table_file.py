from typing import List

from gws_core.config.config_types import ConfigParams
from gws_core.resource import multi_views
from gws_core.resource.multi_views import MultiViews

from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from ..file.file import File
from ..file.file_helper import FileHelper
from ..table.table import Table
from ..table.view.boxplot_view import BoxPlotView
from .view.histogram_view import HistogramView
from .view.lineplot_2d_view import LinePlot2DView
from .view.lineplot_3d_view import LinePlot3DView
from .view.scatterplot_2d_view import ScatterPlot2DView
from .view.scatterplot_3d_view import ScatterPlot3DView
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

    @view(view_type=TableView, human_name='Tabular', short_description='View as a table', default_view=True)
    def view_as_table(self, params: ConfigParams) -> TableView:
        """
        View as table
        """

        return self._get_table_resource().view_as_table(params)

    @view(view_type=LinePlot2DView, human_name='LinePlot2D', short_description='View columns as 2D-line plots', specs={})
    def view_as_line_plot_2d(self, params: ConfigParams) -> LinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return self._get_table_resource().view_as_line_plot_2d(params)

    @view(view_type=LinePlot3DView, human_name='LinePlot3D', short_description='View columns as 3D-line plots', specs={})
    def view_as_line_plot_3d(self, params: ConfigParams) -> LinePlot3DView:
        """
        View columns as 3D-line plots
        """

        return self._get_table_resource().view_as_line_plot_3d(params)

    @view(view_type=ScatterPlot3DView, human_name='ScatterPlot3D', short_description='View columns as 3D-scatter plots',
          specs={})
    def view_as_scatter_plot_3d(self, params: ConfigParams) -> ScatterPlot3DView:
        """
        View columns as 3D-scatter plots
        """

        return self._get_table_resource().view_as_scatter_plot_3d(params)

    @view(view_type=ScatterPlot2DView, human_name='ScatterPlot2D', short_description='View columns as 2D-scatter plots',
          specs={})
    def view_as_scatter_plot_2d(self, params: ConfigParams) -> ScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return self._get_table_resource().view_as_scatter_plot_2d(params)

    @view(view_type=HistogramView, human_name='Histogram', short_description='View columns as 2D-line plots',
          specs={})
    def view_as_histogram(self, params: ConfigParams) -> HistogramView:
        """
        View columns as 2D-line plots
        """

        return self._get_table_resource().view_as_histogram(params)

    @view(view_type=BoxPlotView, human_name='BoxPlot', short_description='View columns as box plots', specs={})
    def view_as_box_plot(self, params: ConfigParams) -> BoxPlotView:
        """
        View one or several columns as box plots
        """

        return self._get_table_resource().view_as_box_plot(params)

    @view(view_type=MultiViews, human_name='Multi view', short_description='Multi view', specs={})
    def view_as_multi_views(self, params: ConfigParams) -> MultiViews:
        """
        View one or several columns as box plots
        """

        multi_views: MultiViews = MultiViews(nb_of_columns=4)
        multi_views.add_view(self.view_as_scatter_plot_2d(params), {}, 3, 1)
        multi_views.add_view(self.view_as_line_plot_2d(params), {}, 1, 3)
        multi_views.add_empty_block(2, 2)
        # multi_views.add_view(self.view_as_table().to_dict(), 2, 2)
        multi_views.add_view(self.view_as_json(params), {}, 1, 2)

        return multi_views

    def _get_table_resource(self) -> Table:
        # guess the delimiter
        delimiter = FileHelper.detect_csv_delimiter(self.read())
        return Table.import_from_path(self, ConfigParams(delimiter=delimiter, header=0))
