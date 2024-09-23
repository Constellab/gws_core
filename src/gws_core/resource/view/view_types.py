

from enum import Enum
from typing import Dict, Union

from gws_core.model.typing_style import TypingIconColor, TypingStyle

from ...config.param.param_spec import ParamSpec
from .lazy_view_param import LazyViewParam

ViewSpecs = Dict[str, Union[ParamSpec, LazyViewParam]]


class ViewType(Enum):
    """List of supported view type
    """
    VIEW = "view"
    JSON = "json-view"
    TEXT = "text-view"
    TABLE = "table-view"
    TABULAR = "tabular-view"
    FOLDER = "folder-view"
    SCATTER_PLOT_2D = "scatter-plot-2d-view"
    VULCANO_PLOT = "vulcano-plot-view"
    LINE_PLOT_2D = "line-plot-2d-view"
    BAR_PLOT = "bar-plot-view"
    STACKED_BAR_PLOT = "stacked-bar-plot-view"
    HISTOGRAM = "histogram-view"
    BOX_PLOT = "box-plot-view"
    HEATMAP = "heatmap-view"
    VENN_DIAGRAM = "venn-diagram-view"
    RESOURCES_LIST_VIEW = "resources-list-view"
    EMPTY = "empty-view"
    MULTI_VIEWS = "multi-view"
    NETWORK = "network-view"
    IMAGE = "image-view"
    HTML = "html-view"
    PLOTLY = "plotly-view"
    RICH_TEXT = "rich-text-view"
    STREAMLIT = "streamlit-view"
    AUDIO = "audio-view"

    def get_typing_style(self) -> TypingStyle:
        """Return the default typing style for the view type
        """

        style: TypingStyle
        if self == ViewType.VIEW:
            style = TypingStyle.default_view()
        elif self == ViewType.JSON:
            style = TypingStyle.material_icon("data_object", background_color="#f6995c")
        elif self == ViewType.TEXT:
            style = TypingStyle.material_icon("text_snippet", background_color="#e4debe")
        elif self == ViewType.TABLE or self == ViewType.TABULAR:
            style = TypingStyle.material_icon("table_chart", background_color="#79ac78")
        elif self == ViewType.FOLDER:
            style = TypingStyle.material_icon("folder", background_color="#7b9dd2")
        elif self == ViewType.SCATTER_PLOT_2D:
            style = TypingStyle.material_icon("scatter_plot")
        elif self == ViewType.VULCANO_PLOT:
            style = TypingStyle.material_icon("assessment")
        elif self == ViewType.LINE_PLOT_2D:
            style = TypingStyle.material_icon("ssid_chart")
        elif self == ViewType.BAR_PLOT:
            style = TypingStyle.material_icon("bar_chart")
        elif self == ViewType.STACKED_BAR_PLOT:
            style = TypingStyle.material_icon("stacked_bar_chart")
        elif self == ViewType.HISTOGRAM:
            style = TypingStyle.material_icon("bar_chart")
        elif self == ViewType.BOX_PLOT:
            style = TypingStyle.material_icon("assessment")
        elif self == ViewType.HEATMAP:
            style = TypingStyle.material_icon("assessment")
        elif self == ViewType.VENN_DIAGRAM:
            style = TypingStyle.material_icon("assessment")
        elif self == ViewType.RESOURCES_LIST_VIEW:
            style = TypingStyle.material_icon("format_list_bulleted", background_color="#496989")
        elif self == ViewType.EMPTY:
            style = TypingStyle.material_icon("assessment")
        elif self == ViewType.MULTI_VIEWS:
            style = TypingStyle.material_icon("assessment")
        elif self == ViewType.NETWORK:
            style = TypingStyle.material_icon("hub", background_color="#627254")
        elif self == ViewType.IMAGE:
            style = TypingStyle.material_icon("image")
        elif self == ViewType.HTML:
            style = TypingStyle.material_icon("computer")
        elif self == ViewType.PLOTLY:
            style = TypingStyle.material_icon("analytics", background_color="#496989")
        elif self == ViewType.RICH_TEXT:
            style = TypingStyle.material_icon("text_snippet", background_color="#f6f193")
        elif self == ViewType.STREAMLIT:
            style = TypingStyle.material_icon("dashboard", background_color='#ff4b4b')
        elif self == ViewType.AUDIO:
            style = TypingStyle.material_icon("audiotrack", background_color="#f6995c")
        else:
            style = TypingStyle.default_view()

        style.fill_empty_values()
        return style

    def get_human_name(self) -> str:
        """Return the name of the view type
        """
        if self == ViewType.VIEW:
            return "View"
        elif self == ViewType.JSON:
            return "JSON"
        elif self == ViewType.TEXT:
            return "Text"
        elif self == ViewType.TABLE or self == ViewType.TABULAR:
            return "Table"
        elif self == ViewType.FOLDER:
            return "Folder"
        elif self == ViewType.SCATTER_PLOT_2D:
            return "Scatter plot 2D"
        elif self == ViewType.VULCANO_PLOT:
            return "Vulcano plot"
        elif self == ViewType.LINE_PLOT_2D:
            return "Line plot 2D"
        elif self == ViewType.BAR_PLOT:
            return "Bar plot"
        elif self == ViewType.STACKED_BAR_PLOT:
            return "Stacked bar plot"
        elif self == ViewType.HISTOGRAM:
            return "Histogram"
        elif self == ViewType.BOX_PLOT:
            return "Box plot"
        elif self == ViewType.HEATMAP:
            return "Heatmap"
        elif self == ViewType.VENN_DIAGRAM:
            return "Venn diagram"
        elif self == ViewType.RESOURCES_LIST_VIEW:
            return "Resources list"
        elif self == ViewType.EMPTY:
            return "Empty"
        elif self == ViewType.MULTI_VIEWS:
            return "Multi views"
        elif self == ViewType.NETWORK:
            return "Network"
        elif self == ViewType.IMAGE:
            return "Image"
        elif self == ViewType.HTML:
            return "HTML"
        elif self == ViewType.PLOTLY:
            return "Plotly"
        elif self == ViewType.RICH_TEXT:
            return "Rich text"
        elif self == ViewType.STREAMLIT:
            return "Streamlit"
        elif self == ViewType.AUDIO:
            return "Audio"
        else:
            return "Unknown"


# List of view type that cannot be used in a note
exluded_views_in_note = [
    ViewType.VIEW, ViewType.FOLDER, ViewType.RESOURCES_LIST_VIEW, ViewType.EMPTY,
    ViewType.RICH_TEXT, ViewType.STREAMLIT, ViewType.AUDIO]
