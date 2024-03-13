

import pandas as pd
import plotly.express as px

from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.model.typing_style import TypingStyle

from ....config.config_params import ConfigParams
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ..plotly_resource import PlotlyResource
from .plotly_task import PlotlyTask


@task_decorator(unique_name="PlotlyViolinplot", human_name="Violinplot Plotly",
                short_description="Violin plot from plotly",
                style=TypingStyle.material_icon("multiline_chart"))
class PlotlyViolinplot(PlotlyTask):
    """
    Plotly violin plot
    plotly.express.violin()

    please check : [https://plotly.com/python-api-reference/generated/plotly.express.violin.html] for more info

    """
    input_specs = PlotlyTask.input_specs

    output_specs = PlotlyTask.output_specs

    config_specs = {
        # base params
        **PlotlyTask.config_specs_d2,
        **PlotlyTask.custom_data,
        'violinmode': StrParam(
            default_value='group',
            optional=True,
            human_name="Violin Mode",
            allowed_values=['group', 'overlay'],
            short_description="violin mode ('group' or 'overlay')",
        ),
        'points': StrParam(
            default_value='outliers',
            optional=True,
            human_name="points",
            short_description="shows outliers",
            allowed_values=["outliers", 'suspectoutliers', 'all', False]
        ),
        'box': BoolParam(
            default_value=False,
            optional=True,
            human_name="notches",
            short_description="if True, boxes are drawn with notches"
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

        # Créez le graphique à l'aide de px.box
        fig = px.violin(
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
            violinmode=params['violinmode'],
            points=params['points'],
            box=params["box"],
            custom_data=params['custom_data'],
        )

        # Mise à jour des axes
        fig.update_xaxes(title=params['x_axis_name'])
        fig.update_yaxes(title=params['y_axis_name'])

        return {"output_plot": PlotlyResource(fig)}
