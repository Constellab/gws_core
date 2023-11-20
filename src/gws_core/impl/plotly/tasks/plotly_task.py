from gws_core.config.param.param_spec import FloatParam, StrParam, BoolParam, ListParam, IntParam
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs

from ....config.config_params import ConfigParams
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ..plotly_resource import PlotlyResource
from ...table.table import Table
import pandas as pd

import plotly.express as px


# from plotly.subplots import make_subplots


# **PlotlyTAsk.config_specs

@task_decorator("PlotlyTask", human_name="Task Plotly",
                short_description="General Plotly Task", hide=True)
class PlotlyTask(Task):
    css_colours = [
        "black", "white", "red", "green", "blue", "yellow", "orange", "pink",
        "purple", "brown", "gray", "cyan", "magenta", "lime", "teal", "navy"]
    css_color_range = [
        'aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose',   'balance',
        'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg', 'brwnyl',
        'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl', 'darkmint',
        'deep', 'delta', 'dense', 'earth', 'edge', 'electric', 'emrld', 'fall',
        'geyser', 'gnbu', 'gray', 'greens', 'greys', 'haline', 'hot', 'hsv',
        'ice', 'icefire', 'inferno', 'jet', 'magenta', 'magma', 'matter',
        'mint', 'mrybm', 'mygbm', 'oranges', 'orrd', 'oryel', 'oxy', 'peach',
        'phase', 'picnic', 'pinkyl', 'piyg', 'plasma', 'plotly3', 'portland',
        'prgn', 'pubu', 'pubugn', 'puor', 'purd', 'purp', 'purples', 'purpor',
        'rainbow', 'rdbu', 'rdgy', 'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds',
        'solar', 'spectral', 'speed', 'sunset', 'sunsetdark', 'teal',
        'tealgrn', 'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid',
        'turbo', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr', 'ylorrd'
    ]
    input_specs = InputSpecs({'input_table': InputSpec(Table, human_name="Table")})

    output_specs = OutputSpecs({'output_plot': OutputSpec(PlotlyResource, human_name="Plotly figure")})
    config_specs_facet = {
        # facet params
        'facet_row': StrParam(
            default_value=None,
            optional=True,
            human_name="Facet Row",
            short_description="str: Values from this column are used to assign marks to facetted subplots in the vertical direction.",
            visibility="protected"
        ),
        'facet_col': StrParam(
            default_value=None,
            optional=True,
            human_name="Facet Column",
            short_description="Values from this column are used to assign marks to facetted subplots in the horizontal direction.",
            visibility="protected"
        ),
        'facet_col_wrap': IntParam(
            default_value=0,
            optional=True,
            human_name="Facet Col Wrap",
            short_description="int: Maximum number of facet columns. ",
            visibility="protected"
        ),
        'facet_row_spacing': FloatParam(
            default_value=None,
            optional=True,
            human_name="Facet row Spacing",
            short_description="float: Spacing between facet rows, in paper units. Default is 0.03 or 0.0.7 when facet_col_wrap is used.",
            visibility="protected"
        ),
        'facet_col_spacing': FloatParam(
            default_value=None,
            optional=True,
            human_name="Facet col Spacing",
            short_description="float: Spacing between facet columns, in paper units. Default is 0.03 or 0.0.7 when facet_col_wrap is used.",
            visibility="protected"
        ), }
    config_specs_hover = {
        # pas dans tous
        'hover_data': ListParam(
            default_value=None,
            optional=True,
            human_name="Hover Data",
            short_description="list str: Values from these columns appear in the hover tooltip.",
            visibility="protected"
        ),
        # hover params
        'hover_name': StrParam(
            default_value=None,
            optional=True,
            human_name="Hover Name",
            short_description="Values from this column appear in bold in the hover tooltip.",
            visibility="protected"
        ),
    }
    layout = {
        'title': StrParam(
            default_value=None,
            optional=True,
            human_name="Title",
            short_description="Title of the graph"
        ),
        'y_axis_name': StrParam(
            default_value=None,
            optional=True,
            human_name="Y Axis Name",
            short_description="set the y axis name"
        ),
        'x_axis_name': StrParam(
            default_value=None,
            optional=True,
            human_name="X Axis Name",
            short_description="set the x axis name"
        ),
        'template': StrParam(
            default_value=None,
            optional=True,
            human_name="Template",
            short_description="Plotly template to use",
            visibility="protected",
            allowed_values=[
                "ggplot2", "seaborn", "simple_white", "plotly", "plotly_dark",
                "presentation", "xgridoff", "ygridoff", "gridon", "none"
            ]
        ),
        'animation_frame': StrParam(
            default_value=None,
            optional=True,
            human_name="Animation Frame",
            short_description="str: Values from this column are used to assign marks to animation frames.",
            visibility="protected"
        ),
        'animation_group': StrParam(
            default_value=None,
            optional=True,
            human_name="Animation Group",
            short_description="str: Values from this column are used to provide object-constancy across animation frames: rows with matching `animation_group`s will be treated as if they describe the same object in each frame.",
            visibility="protected"
        ),
        'category_orders': StrParam(
            default_value=None,
            optional=True,
            human_name="category orders",
            visibility="private"
        ),
        'log_x': BoolParam(
            default_value=False,
            optional=True,
            human_name="Log X Axis",
            short_description=" the x-axis is log-scaled in cartesian coordinates.",
            visibility="protected"
        ),
        'log_y': BoolParam(
            default_value=False,
            optional=True,
            human_name="Log Y Axis",
            short_description=" the y-axis is log-scaled in cartesian coordinates.",
            visibility="protected"
        ),
        'range_x': StrParam(
            default_value=None,
            optional=True,
            human_name="X Axis Range",
            short_description="If provided, overrides auto-scaling on the x-axis in cartesian coordinates.",
            visibility="protected"
        ),
        'range_y': StrParam(
            default_value=None,
            optional=True,
            human_name="Y Axis Range",
            short_description=" If provided, overrides auto-scaling on the y-axis in cartesian coordinates.",
            visibility="protected"
        ),
        'width': IntParam(
            default_value=None,
            optional=True,
            human_name="Width",
            short_description="int: The figure width in pixels.",
            visibility="protected"
        ),
        'height': IntParam(
            default_value=None,
            optional=True,
            human_name="Height",
            short_description="int The figure height in pixels",
            visibility="protected"
        ),
        'label_columns': ListParam(
            default_value=None,
            optional=True,
            visibility='protected',
            human_name='columns to label',
            short_description="one column per line, and same line for the text",
        ),
        'label_text': ListParam(
            default_value=None,
            optional=True,
            visibility="protected",
            human_name='text for labelling',
            short_description="text for labels, size should match 'colot to label'"
        ),
        **config_specs_facet,
        **config_specs_hover,
        'color_discrete_sequence': StrParam(
            default_value=None,
            optional=True,
            human_name="color discrete sequence",
            visibility="private"
        ),
        'color_discrete_map': StrParam(
            default_value=None,
            optional=True,
            human_name="color discrete map",
            visibility="private"
        ),
        'orientation': StrParam(
            default_value='v',
            optional=True,
            human_name="Orientation",
            short_description="Orientation of the box plot ('v' for vertical, 'h' for horizontal)",
            allowed_values=['v', 'h'],
            visibility="protected"
        )
    }
    config_specs_d2 = {
        # base params
        'x': StrParam(
            default_value=None,
            human_name="x-axis",
            short_description="str: column name for x-axis' values"
        ),
        'y': StrParam(
            default_value=None,
            optional=True,
            human_name="y-axis",
            short_description="str: column name for y-axis' values"),
        'color': StrParam(
            default_value=None,
            optional=True,
            human_name="Color",
            short_description="str: column name to color the graph figures"
        ),
        **layout
    }
    errors = {  # line, bar, scatter

        'error_x': StrParam(
            default_value=None,
            optional=True,
            human_name="x error",
            short_description="str: Values from this column are used to size x-axis error bars",
            visibility='protected'
        ),
        'error_x_minus': StrParam(
            default_value=None,
            optional=True,
            human_name="min X error",
            short_description="str: Values from this column or array_like are used to size x-axis error bars in the negative direction.",
            visibility='protected'
        ),
        'error_y': StrParam(
            default_value=None,
            optional=True,
            human_name="y error",
            short_description="str: Values from this column are used to size y-axis error bars",
            visibility='protected'
        ),
        'error_y_minus': StrParam(
            default_value=None,
            optional=True,
            human_name="min y error",
            short_description="str: Values from this column or array_like are used to size x-axis error bars in the negative direction.",
            visibility='protected'
        ),
        'text': StrParam(
            default_value=None,
            optional=True,
            human_name="text labels",
            short_description="str: Values from this column or array_like appear in the figure as text labels."
        ),
    }
    pattern_shape = {  # bar, histogram
        'pattern_shape': StrParam(
            default_value=None,
            optional=True,
            human_name="pattern shape",
            visibility="private"
        ),
        'pattern_shape_sequence': StrParam(
            default_value=None,
            optional=True,
            human_name="pattern shape sequence",
            visibility="private"
        ),
        'pattern_shape_map': StrParam(
            default_value=None,
            optional=True,
            human_name="pattern shape map",
            visibility="private"
        )
    }
    color_continuous = {  # bar, scatter
        'color_continuous_scale': StrParam(
            default_value=None,
            optional=True,
            visibility="private",
            human_name="color continuous scale",
        ),
        'color_continuous_midpoint': IntParam(
            default_value=None,
            optional=True,
            visibility="private",
            human_name="color continuous midpoint",
        ),
        'range_color': ListParam(
            default_value=None,
            optional=True,
            human_name="range colors",
            visibility="private"
        ),
    }
    symbol = {  # scatter, line
        'symbol': StrParam(
            default_value=None,
            optional=True,
            human_name='symbol',
            short_description="str: Values from this column are used to assign symbols to marks.",
        ),
        'symbol_sequence': StrParam(
            default_value=None,
            optional=True,
            human_name='symbol sequence',
            visibility="private"
        ),
        'symbol_map': StrParam(
            default_value=None,
            optional=True,
            human_name='symbol map',
            visibility="private"
        ),

        'render_mode': StrParam(
            default_value=None,
            optional=True,
            human_name="Render Mode",
            allowed_values=["svg", "webgl", "auto"],
            short_description="Controls the browser API used to draw marks. ",
            visibility="protected"
        ),
    }
    trendline = {  # scatter
        'trendline': StrParam(
            default_value=None,
            optional=True,
            human_name="Trendline",
            short_description="Add a trendline to the plot, see the plotlydoc : plotly.express.trendline_functions",
            visibility="protected",
            allowed_values=['ols', 'lowess', 'rolling', 'expanding', 'ewm']
        ),
        'trendline_options': StrParam(
            default_value=None,
            optional=True,
            human_name='trendline options',
            visibility="private"
        ),
        'trendline_color_override': StrParam(
            default_value=None,
            optional=True,
            visibility='protected',
            human_name="trendline color",
            short_description="all trendlines will be drawn in this color rather than in the same color as the traces from which they draw their inputs.",
            allowed_values=css_colours
        ),
        'trendline_scope': StrParam(
            default_value='trace',
            optional=True,
            visibility="protected",
            human_name='trendline scope',
            short_description="If 'trace', then one trendline is drawn per trace (i.e. per color, symbol, facet, animation frame etc) and if 'overall' then one trendline is computed for the entire dataset, and replicated across all facets.",
            allowed_values=['trace', 'overall']
        ),
    }
    bar_opt = {  # bar, histogram
        'opacity': FloatParam(
            default_value=None,
            optional=True,
            human_name="Opacity",
            short_description="float:  Value between 0 and 1. Sets the opacity for markers.",
            visibility="protected",
        ),
        'barmode': StrParam(
            default_value=None,
            optional=True,
            human_name="Bar Mode",
            short_description="Bar mode for stacked or grouped histograms",
            allowed_values=['stack', 'group', 'overlay', 'relative'],
            visibility="protected",
        ),
        'text_auto': BoolParam(
            default_value=False,
            optional=True,
            visibility='private',
            human_name='text auto',
        )
    }
    custom_data = {
        'custom_data': StrParam(
            default_value=None,
            optional=True,
            human_name='custom data',
            short_description="str: Values from this column are displayed on the graph"
        )
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        pass
