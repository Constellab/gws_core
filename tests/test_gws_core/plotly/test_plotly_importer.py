from unittest import TestCase

import plotly.express as px
from pandas import DataFrame

from gws_core.impl.file.file import File
from gws_core.impl.plotly.plotly_resource import PlotlyResource
from gws_core.impl.plotly.tasks.plotly_importer import PlotlyExporter, PlotlyImporter


# test_plotly_importer
class TestPlotlyImporter(TestCase):
    def test_plotly_exporter_importer(self):
        dataframe = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        figure = px.scatter(dataframe, x="A", y="B")

        plotlyResource = PlotlyResource(figure)

        result_path: File = PlotlyExporter.call(plotlyResource)

        self.assertTrue(result_path.path.endswith(".json"))
        self.assertTrue(result_path.exists())
        self.assertFalse(result_path.is_empty())

        imported_resource = PlotlyImporter.call(result_path)

        self.assertIsInstance(imported_resource, PlotlyResource)
        self.assertTrue(plotlyResource.equals(imported_resource))
