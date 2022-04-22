# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import Any, Dict, TypedDict, Union

from ..config.param_spec import ParamSpec
from .lazy_view_param import LazyViewParam

ViewSpecs = Dict[str, Union[ParamSpec, LazyViewParam]]


class ViewType(Enum):
    """List of supported view type
    """
    VIEW = "view"
    JSON = "json-view"
    TEXT = "text-view"
    TABLE = "table-view"
    DATASET = "dataset-view"
    FOLDER = "folder-view"
    SCATTER_PLOT_2D = "scatter-plot-2d-view"
    SCATTER_PLOT_3D = "scatter-plot-3d-view"
    LINE_PLOT_2D = "line-plot-2d-view"
    LINE_PLOT_3D = "line-plot-3d-view"
    BAR_PLOT = "bar-plot-view"
    STACKED_BAR_PLOT = "stacked-bar-plot-view"
    HISTOGRAM = "histogram-view"
    BOX_PLOT = "box-plot-view"
    HEATMAP = "heatmap-view"
    VENN_DIAGRAM = "venn-diagram-view"
    RESOURCES_LIST_VIEW = "resources-list-view"
    EMPTY = "empty-view"
    MULTI_VIEWS = "multi-view"
