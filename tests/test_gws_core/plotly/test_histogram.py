# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

import pandas as pd
import plotly.express as px

from gws_core.config.config_params import ConfigParams
from gws_core.impl.plotly.plotly_resource import PlotlyResource
from gws_core.impl.plotly.tasks.plotly_histogram import PlotlyHistogram
from gws_core.impl.table.table import Table
from gws_core.task.task_runner import TaskRunner


class TestHistogram(TestCase):
    def test_histogram(self):
        # Créez un DataFrame de test
        df = pd.DataFrame({
            'x': [1],
            'y': [10],
            'z': [5.5],
            'a': ['b'],
            'c': ['d'],
            'e': ['f']
        })

        runner = TaskRunner(
            task_type=PlotlyHistogram,
            inputs={'input_table': Table(df)},
            params={
                'x': 'x',
                'y': 'y',
                'colour': 'z',
                'title': 'title',
                'x_axis_name': 'x_axis_name',
                'y_axis_name': 'y_axis_name',
                'log_x': True,
                'log_y': False,
                # Autres paramètres...
            }
        )

        outputs = runner.run()
        plot_output: PlotlyResource = outputs['output_plot']
        expected_output = px.histogram(data_frame=df, x='x', y='y', color='z',
                                       title='title', log_x=True, log_y=False)
        expected_output.update_yaxes(title='y_axis_name')
        expected_output.update_xaxes(title='x_axis_name')
        expected_output = PlotlyResource(expected_output)
        self.assertIsNotNone(plot_output.default_view(ConfigParams()).to_dto(ConfigParams()))

    # Ajoutez d'autres méthodes de test pour tester différentes configurations et paramètres...
