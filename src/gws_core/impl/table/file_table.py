from typing import List

from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.table.table import Table

from ...config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from ..file.file import File
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

    @view(view_type=LinePlot2DView, human_name='LinePlot2D', short_description='View columns as 2D-line plots',
          specs={
              "x_column_name": StrParam(human_name="X-column name", short_description="The column to use as x-axis"),
              "y_column_names": ListParam(human_name="Y-column names", short_description="List of columns to use as y-axis")
          })
    def view_as_line_plot_2d(self, *args, **kwargs) -> LinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return self._get_table_resource().view_as_line_plot_2d(*args, **kwargs)

    @view(view_type=LinePlot3DView, human_name='LinePlot3D', short_description='View columns as 3D-line plots',
          specs={
              "x_column_name": StrParam(human_name="X-column name", short_description="The column to use as x-axis"),
              "y_column_name": StrParam(human_name="Y-column name", short_description="The column to use as y-axis"),
              "z_column_names": ListParam(human_name="Z-column names", short_description="List of columns to use as z-axis"),
          })
    def view_as_line_plot_3d(self, *args, **kwargs) -> LinePlot3DView:
        """
        View columns as 3D-line plots
        """

        return self._get_table_resource().view_as_line_plot_3d(*args, **kwargs)

    @view(view_type=ScatterPlot3DView, human_name='ScatterPlot3D', short_description='View columns as 3D-scatter plots',
          specs={
              "x_column_name": StrParam(human_name="X-column name", short_description="The column to use as x-axis"),
              "y_column_names": ListParam(human_name="Y-column names", short_description="List of columns to use as y-axis")
          })
    def view_as_scatter_plot_3d(self, *args, **kwargs) -> ScatterPlot3DView:
        """
        View columns as 3D-scatter plots
        """

        return self._get_table_resource().view_as_scatter_plot_3d(*args, **kwargs)

    @view(view_type=ScatterPlot2DView, human_name='ScatterPlot2D', short_description='View columns as 2D-scatter plots',
          specs={
              "x_column_name": StrParam(human_name="X-column name", short_description="The column to use as x-axis"),
              "y_column_names": ListParam(human_name="Y-column names", short_description="List of columns to use as y-axis")
          })
    def view_as_scatter_plot_2d(self, *args, **kwargs) -> ScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return self._get_table_resource().view_as_scatter_plot_2d(*args, **kwargs)

    @view(view_type=HistogramView, human_name='Histogram', short_description='View columns as 2D-line plots',
          specs={
              "column_names": ListParam(human_name="Column names", short_description="List of columns to view"),
              "nbins": IntParam(default_value=10, min_value=0, human_name="Nbins", short_description="The number of bins. Set zero (0) for auto."),
              "density": BoolParam(default_value=False, human_name="Density", short_description="True to pplot density")
          })
    def view_as_histogram(self, *args, **kwargs) -> HistogramView:
        """
        View columns as 2D-line plots
        """

        return self._get_table_resource().view_as_histogram(*args, **kwargs)

    def _get_table_resource(self) -> Table:
        # guess the delimiter
        delimiter = FileHelper.detect_csv_delimiter(self.read())
        return Table.import_from_path(file_path=self.path, delimiter=delimiter)
