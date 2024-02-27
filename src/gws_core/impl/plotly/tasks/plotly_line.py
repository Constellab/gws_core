# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import pandas as pd
import plotly.express as px

from gws_core.config.param.param_spec import BoolParam, StrParam

from ....config.config_params import ConfigParams
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ..plotly_resource import PlotlyResource
from .plotly_task import PlotlyTask

# from plotly.subplots import make_subplots


@task_decorator("PlotlyLine", human_name="Line Plotly",
                short_description="line plot from plotly", icon="ssid_chart")
class PlotlyLine(PlotlyTask):
    """
    Plotly linear plot
    plotly.express.line()

    please check : [https://plotly.com/python-api-reference/generated/plotly.express.line.html] for more info
    """
    input_specs = PlotlyTask.input_specs

    output_specs = PlotlyTask.output_specs

    config_specs = {
        **PlotlyTask.config_specs_d2,
        **PlotlyTask.custom_data,
        'line_group': StrParam(
            default_value=None,
            optional=True,
            human_name=" Group by line",
            short_description="group rows by line"
        ),
        'line_dash': StrParam(
            default_value=None,
            optional=True,
            visibility="private",
            human_name="Values from this column are used to assign dash-patterns to lines.",
        ),
        'line_dash_sequence': StrParam(
            default_value=None,
            optional=True,
            visibility="private",
            human_name="line dash sequence",

        ),
        'line_dash_map': StrParam(
            default_value=None,
            optional=True,
            visibility="private",
            human_name="line dash map",
        ),
        'markers': BoolParam(
            default_value=False,
            human_name="Marker",
            optional=True,
            short_description="if ticked, markers are shown on line"
        ),
        'line_shape': StrParam(
            default_value=None,
            optional=True,
            human_name="line shape",
            allowed_values=["linear", "spline"],
            visibility="protected",
            short_description=""
        ),
        **PlotlyTask.symbol,
        **PlotlyTask.errors,
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # Get the data frame from the input
        dataframe = pd.DataFrame(inputs['input_table'].get_data())
        for key, i in params.items():
            if i == "":
                params[key] = None
        if params['label_columns'] is not None:
            labels = dict(zip(params['label_columns'], params['label_text']))
        else:
            labels = None

        # Create the line plot using Plotly Express
        fig = px.line(
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
            line_shape=params['line_shape'],
            line_dash=params['line_dash'],
            line_dash_sequence=params['line_dash_sequence'],
            line_dash_map=params['line_dash_map'],
            markers=params['markers'],
            custom_data=params['custom_data'],
            # errors
            error_x=params['error_x'],
            error_x_minus=params['error_x_minus'],
            error_y=params['error_y'],
            error_y_minus=params['error_y_minus'],
            text=params['text'],
            # symbols
            symbol=params['symbol'],
            symbol_map=params['symbol_map'],
            symbol_sequence=params['symbol_sequence'],
            render_mode=params['render_mode'],
        )

        # Update axis titles
        fig.update_xaxes(title=params['x_axis_name'])
        fig.update_yaxes(title=params['y_axis_name'])

        return {"output_plot": PlotlyResource(fig)}
