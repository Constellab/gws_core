from typing import List

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


@resource_decorator("FileTable")
class FileTable(File):
    """Specific file to .csv and .tsv files. This file contains the sames view as the Table resource.

    :param File: [description]
    :type File: [type]
    :return: [description]
    :rtype: [type]
    """

    supported_extensions: List[str] = ['xlsx', 'xls', 'csv', 'tsv']

    @view(view_type=TableView, human_name='Tabular', short_description='View as a table', default_view=True)
    def view_as_table(self) -> TableView:
        """
        View as table
        """

        return self._get_table_resource().view_as_table()

    @view(view_type=LinePlot2DView, human_name='LinePlot2D', short_description='View columns as 2D-line plots', specs={})
    def view_as_line_plot_2d(self, *args, **kwargs) -> LinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return self._get_table_resource().view_as_line_plot_2d(*args, **kwargs)

    @view(view_type=LinePlot3DView, human_name='LinePlot3D', short_description='View columns as 3D-line plots', specs={})
    def view_as_line_plot_3d(self, *args, **kwargs) -> LinePlot3DView:
        """
        View columns as 3D-line plots
        """

        return self._get_table_resource().view_as_line_plot_3d(*args, **kwargs)

    @view(view_type=ScatterPlot3DView, human_name='ScatterPlot3D', short_description='View columns as 3D-scatter plots',
          specs={})
    def view_as_scatter_plot_3d(self, *args, **kwargs) -> ScatterPlot3DView:
        """
        View columns as 3D-scatter plots
        """

        return self._get_table_resource().view_as_scatter_plot_3d(*args, **kwargs)

    @view(view_type=ScatterPlot2DView, human_name='ScatterPlot2D', short_description='View columns as 2D-scatter plots',
          specs={})
    def view_as_scatter_plot_2d(self, *args, **kwargs) -> ScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return self._get_table_resource().view_as_scatter_plot_2d(*args, **kwargs)

    @view(view_type=HistogramView, human_name='Histogram', short_description='View columns as 2D-line plots',
          specs={})
    def view_as_histogram(self, *args, **kwargs) -> HistogramView:
        """
        View columns as 2D-line plots
        """

        return self._get_table_resource().view_as_histogram(*args, **kwargs)

    @view(view_type=BoxPlotView, human_name='BoxPlot', short_description='View columns as box plots', specs={})
    def view_as_box_plot(self, *args, **kwargs) -> BoxPlotView:
        """
        View one or several columns as box plots
        """

        return self._get_table_resource().view_as_box_plot(*args, **kwargs)

    def _get_table_resource(self) -> Table:
        # guess the delimiter
        delimiter = FileHelper.detect_csv_delimiter(self.read())
        return Table.import_from_path(file_path=self.path, delimiter=delimiter)
