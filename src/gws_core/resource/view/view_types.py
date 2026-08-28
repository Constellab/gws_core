from enum import Enum

from gws_core.model.typing_style import TypingStyle


class ViewType(Enum):
    """List of supported view type"""

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
    MARKDOWN = "markdown-view"
    PLOTLY = "plotly-view"
    RICH_TEXT = "rich-text-view"
    APP = "app-view"
    AUDIO = "audio-view"
    IFRAME = "iframe-view"

    def get_typing_style(self) -> TypingStyle:
        """Return the default typing style for the view type"""

        style: TypingStyle
        icon_style = _VIEW_TYPE_MATERIAL_ICON_STYLES.get(self)
        if icon_style is None:
            # view types without a dedicated material icon fallback on the default view style
            style = TypingStyle.default_view()
        else:
            icon_name, background_color = icon_style
            style = TypingStyle.material_icon(icon_name, background_color=background_color)

        style.fill_empty_values()
        return style

    def get_human_name(self) -> str:
        """Return the name of the view type"""
        return _VIEW_TYPE_HUMAN_NAMES.get(self, "Unknown")


# Material icon (icon name, background color) used to build the default typing style of a view type.
# View types absent from this mapping (VIEW, IFRAME) use TypingStyle.default_view().
_VIEW_TYPE_MATERIAL_ICON_STYLES: dict[ViewType, tuple[str, str | None]] = {
    ViewType.JSON: ("data_object", "#f6995c"),
    ViewType.TEXT: ("text_snippet", "#e4debe"),
    ViewType.TABLE: ("table_chart", "#79ac78"),
    ViewType.TABULAR: ("table_chart", "#79ac78"),
    ViewType.FOLDER: ("folder", "#7b9dd2"),
    ViewType.SCATTER_PLOT_2D: ("scatter_plot", None),
    ViewType.VULCANO_PLOT: ("assessment", None),
    ViewType.LINE_PLOT_2D: ("ssid_chart", None),
    ViewType.BAR_PLOT: ("bar_chart", None),
    ViewType.STACKED_BAR_PLOT: ("stacked_bar_chart", None),
    ViewType.HISTOGRAM: ("bar_chart", None),
    ViewType.BOX_PLOT: ("assessment", None),
    ViewType.HEATMAP: ("assessment", None),
    ViewType.VENN_DIAGRAM: ("assessment", None),
    ViewType.RESOURCES_LIST_VIEW: ("format_list_bulleted", "#496989"),
    ViewType.EMPTY: ("assessment", None),
    ViewType.MULTI_VIEWS: ("assessment", None),
    ViewType.NETWORK: ("hub", "#627254"),
    ViewType.IMAGE: ("image", None),
    ViewType.MARKDOWN: ("computer", None),
    ViewType.PLOTLY: ("analytics", "#496989"),
    ViewType.RICH_TEXT: ("text_snippet", "#f6f193"),
    ViewType.APP: ("dashboard", "#ff4b4b"),
    ViewType.AUDIO: ("volume_up", "#f6995c"),
}

# Human readable name of each view type. Unmapped view types are named 'Unknown'.
_VIEW_TYPE_HUMAN_NAMES: dict[ViewType, str] = {
    ViewType.VIEW: "View",
    ViewType.JSON: "JSON",
    ViewType.TEXT: "Text",
    ViewType.TABLE: "Table",
    ViewType.TABULAR: "Table",
    ViewType.FOLDER: "Folder",
    ViewType.SCATTER_PLOT_2D: "Scatter plot 2D",
    ViewType.VULCANO_PLOT: "Vulcano plot",
    ViewType.LINE_PLOT_2D: "Line plot 2D",
    ViewType.BAR_PLOT: "Bar plot",
    ViewType.STACKED_BAR_PLOT: "Stacked bar plot",
    ViewType.HISTOGRAM: "Histogram",
    ViewType.BOX_PLOT: "Box plot",
    ViewType.HEATMAP: "Heatmap",
    ViewType.VENN_DIAGRAM: "Venn diagram",
    ViewType.RESOURCES_LIST_VIEW: "Resources list",
    ViewType.EMPTY: "Empty",
    ViewType.MULTI_VIEWS: "Multi views",
    ViewType.NETWORK: "Network",
    ViewType.IMAGE: "Image",
    ViewType.IFRAME: "Iframe",
    ViewType.MARKDOWN: "Markdown",
    ViewType.PLOTLY: "Plotly",
    ViewType.RICH_TEXT: "Rich text",
    ViewType.APP: "App",
    ViewType.AUDIO: "Audio",
}


# List of view type that cannot be used in a note
exluded_views_in_note = [
    ViewType.VIEW,
    ViewType.FOLDER,
    ViewType.RESOURCES_LIST_VIEW,
    ViewType.EMPTY,
    ViewType.RICH_TEXT,
    ViewType.APP,
]
