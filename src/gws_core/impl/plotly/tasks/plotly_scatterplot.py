

import pandas as pd
import plotly.express as px

from gws_core.config.param.param_spec import FloatParam, IntParam, StrParam
from gws_core.model.typing_style import TypingStyle

from ....config.config_params import ConfigParams
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ..plotly_resource import PlotlyResource
from .plotly_task import PlotlyTask


@task_decorator("PlotlyScatterplot", human_name="Scatterplot Plotly",
                short_description="Scatter plot from plotly(px)",
                style=TypingStyle.material_icon("scatter_plot"))
class PlotlyScatterplot(PlotlyTask):
    """
    Plotly scatter plot
    plotly.express.scatter()

    please check : [https://plotly.com/python-api-reference/generated/plotly.express.scatter.html] for more info
    """

    input_specs = PlotlyTask.input_specs

    output_specs = PlotlyTask.output_specs

    config_specs = {
        **PlotlyTask.config_specs_d2,
        'size': StrParam(
            default_value=None,
            optional=True,
            human_name="size",
            short_description=" Values from this column are used to assign mark sizes"
        ),
        'opacity': FloatParam(
            default_value=None,
            visibility='protected',
            human_name="opacity",
            short_description="float: opacity of the marks",
            optional=True
        ),
        'size_max': IntParam(
            default_value=20,
            optional=True,
            visibility='protected',
            short_description="int: maximum size of the marks",
            human_name="mark opacity"
        ),
        'marginal_x': StrParam(
            default_value=None,
            optional=True,
            human_name="Marginal X",
            short_description="If set, a horizontal subplot is drawn above the main plot, visualizing the x-distribution.",
            visibility="protected",
            allowed_values=['rug', 'box', 'violin', 'histogram']
        ),
        'marginal_y': StrParam(
            default_value=None,
            optional=True,
            human_name="Marginal Y",
            short_description="If set, a vertical subplot is drawn to the right of the main plot, visualizing the y-distribution.",
            visibility="protected",
            allowed_values=['rug', 'box', 'violin', 'histogram']
        ),
        **PlotlyTask.symbol,
        **PlotlyTask.errors,
        **PlotlyTask.color_continuous,
        **PlotlyTask.trendline,
        **PlotlyTask.custom_data,
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

        fig = px.scatter(
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
            marginal_x=params['marginal_x'],
            marginal_y=params['marginal_y'],
            size=params['size'],
            size_max=params['size_max'],
            opacity=params['opacity'],
            custom_data=params['custom_data'],
            # trendline
            trendline=params['trendline'],
            trendline_color_override=params['trendline_color_override'],
            trendline_options=params['trendline_options'],
            trendline_scope=params['trendline_scope'],
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
            # color continuous
            color_continuous_midpoint=params['color_continuous_midpoint'],
            color_continuous_scale=params['color_continuous_scale'],
        )

        fig.update_xaxes(title=params["x_axis_name"])
        fig.update_yaxes(title=params['y_axis_name'])
        return {"output_plot": PlotlyResource(fig)}
