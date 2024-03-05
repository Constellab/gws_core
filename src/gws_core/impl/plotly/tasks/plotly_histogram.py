# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas as pd
import plotly.express as px

from gws_core.config.param.param_spec import BoolParam, IntParam, StrParam
from gws_core.model.typing_style import TypingStyle

from ....config.config_params import ConfigParams
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ..plotly_resource import PlotlyResource
from .plotly_task import PlotlyTask


@task_decorator("PlotlyHistogram", human_name="Histogram Plotly",
                short_description="Histogram plot from plotly(px)",
                style=TypingStyle.material_icon("bar_chart"))
class PlotlyHistogram(PlotlyTask):

    input_specs = PlotlyTask.input_specs

    output_specs = PlotlyTask.output_specs

    config_specs = {
        **PlotlyTask.config_specs_d2,
        **PlotlyTask.pattern_shape,
        **PlotlyTask.bar_opt,
        'marginal': StrParam(
            default_value=None,
            optional=True,
            visibility='protected',
            human_name='marginal plot',
            short_description="if set, a subplot is drawn alongside the main plot, visualising the distribution",
            allowed_values=['rug', 'box', 'violin', 'histogram']
        ),
        'barnorm': StrParam(
            default_value=None,
            optional=True,
            visibility='protected',
            human_name="bar normalisation",
            short_description="If 'fraction', the value of each bar is divided by the sum of all values at that location coordinate. 'percent' is the same but multiplied by 100 to show percentages. None will stack up all values at each location coordinate.",
            allowed_values=['fraction', 'percent']
        ),
        'histnorm': StrParam(
            default_value=None,
            optional=True,
            human_name="Normalization",
            short_description="Histogram normalization",
            allowed_values=['percent', 'probability', 'density', 'probability density'],
            visibility="protected",
        ),
        'histfunc': StrParam(
            default_value='count',
            optional=True,
            human_name='histogram function',
            short_description='Function used to aggregate values for summarization',
            allowed_values=['count', 'sum', 'avg', 'min', 'max']
        ),
        'cumulative': BoolParam(
            default_value=False,
            optional=True,
            human_name='cumulative',
            short_description='cumulative or not',
        ),
        'nbins': IntParam(
            default_value=None,
            optional=True,
            visibility='protected',
            short_description='Sets the number of bins',
            human_name='nb of bins'
        ),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        dataframe = pd.DataFrame(inputs['input_table'].get_data())
        for key, i in params.items():
            if i == "":
                params[key] = None
        if params['label_columns'] is not None:
            labels = dict(zip(params['label_columns'], params['label_text']))
        else:
            labels = None

        fig = px.histogram(
            data_frame=dataframe,
            # base params
            x=params['x'],
            y=params['y'],
            title=params['title'],
            color=params['color'],
            # facet params
            facet_row=params['facet_row'],
            facet_col=params['facet_col'],
            facet_col_wrap=params['facet_col_wrap'],
            facet_row_spacing=params['facet_row_spacing'],
            facet_col_spacing=params['facet_col_spacing'],
            # hover params
            hover_name=params['hover_name'],
            hover_data=params['hover_data'],
            # animation params
            animation_frame=params['animation_frame'],
            animation_group=params['animation_group'],
            # layout params
            labels=labels,
            category_orders=params['category_orders'],
            color_discrete_sequence=params['color_discrete_sequence'],
            color_discrete_map=params['color_discrete_map'],
            orientation=params['orientation'],
            log_x=params['log_x'],
            log_y=params['log_y'],
            range_x=params['range_x'],
            range_y=params['range_y'],
            template=params['template'],
            width=params['width'],
            height=params['height'],
            # specific params
            marginal=params['marginal'],
            barnorm=params['barnorm'],
            histnorm=params['histnorm'],
            histfunc=params['histfunc'],
            cumulative=params['cumulative'],
            nbins=params['nbins'],
            # bar opt
            opacity=params['opacity'],
            barmode=params['barmode'],
            text_auto=params['text_auto'],
            # pattern
            # pattern shape
            pattern_shape=params['pattern_shape'],
            pattern_shape_map=params['pattern_shape_map'],
            pattern_shape_sequence=params['pattern_shape_sequence']

        )
        # Mise à jour des axes
        fig.update_xaxes(title=params['x_axis_name'])
        fig.update_yaxes(title=params['y_axis_name'])

        return {"output_plot": PlotlyResource(fig)}
