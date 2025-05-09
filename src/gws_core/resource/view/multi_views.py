

from typing import List

from typing_extensions import TypedDict

from gws_core.resource.view.view_types import ViewType

from ...config.config_params import ConfigParams, ConfigParamsDict
from .view import View


class ViewGrid(TypedDict):
    view: View
    config_params: ConfigParamsDict
    colspan: int
    rowspan: int


class EmptyView(View):
    _type: ViewType = ViewType.EMPTY


class MultiViews(View):
    """Class MultiView. This is use to multiple view in the same page

    The view model is:
    ```
    {
        "type": "multi-view"
        "data":
            "views": [
                {
                    "view": {},
                    "colspan": colspan,
                    "rowspan": rowspan,
                },
                ...
            ],
    }
    ```
    """

    _sub_views: List[ViewGrid]
    _type: ViewType = ViewType.MULTI_VIEWS
    _nb_of_columns: int

    def __init__(self, nb_of_columns: int):
        """[summary]

        :param nb_of_columns: total number of columns of the grid
        :type nb_of_columns: int
        """
        super().__init__()
        self._check_number(nb_of_columns, 'Number of columns')
        self._sub_views = []
        self._nb_of_columns = nb_of_columns

    def add_view(self, view: View, params: ConfigParamsDict = None, colspan: int = 1, rowspan: int = 1) -> None:
        """Add a view to the multi view

        :param view: view
        :type view: Dict[str, Any]
        :param params: values for the config of the view
        :type params: Dict[str, Any]
        :param colspan: Nb of columns taken by the view in the grid, defaults to 1
        :type colspan: int, optional
        :param rowspan: Nb of rows taken by the view in the grid, defaults to 1
        :type rowspan: int, optional
        :raises Exception: [description]
        """

        if not isinstance(view, View):
            raise Exception('[MultiViews] the view input is not a View')

        if isinstance(view, MultiViews):
            raise Exception('[MultiViews] cannot create nested MultiViews')

        config_params: ConfigParamsDict = view._specs.get_and_check_values(params)

        self._check_number(colspan, 'Colums span')
        self._check_number(rowspan, 'Rows span')

        if colspan > self._nb_of_columns:
            raise Exception('[MultiViews] the colums span must not be bigger than the number of columns')

        self._sub_views.append(
            {
                "view": view,
                "config_params": config_params,
                "colspan": colspan,
                "rowspan": rowspan,
            }
        )

    def add_empty_block(self, colspan: int = 1, rowspan: int = 1) -> None:
        """Add en empty block in the grid

          :param colspan: Nb of columns taken by the empty block, defaults to 1
          :type colspan: int, optional
          :param rowspan: Nb of rows taken by the empty block, defaults to 1
          :type rowspan: int, optional
        """
        self._sub_views.append(
            {
                "view": EmptyView(),
                "config_params": {},
                "colspan": colspan,
                "rowspan": rowspan,
            }
        )

    def data_to_dict(self, params: ConfigParams) -> dict:
        views_dict: List[dict] = []
        for sub_view in self._sub_views:
            view_dict = sub_view["view"].to_dto(ConfigParams(sub_view["config_params"])).to_json_dict()
            views_dict.append({
                "view": view_dict,
                "colspan": sub_view["colspan"],
                "rowspan": sub_view["rowspan"],
            })

        return {
            "nb_of_columns": self._nb_of_columns,
            "views": views_dict
        }

    def _check_number(self, nb: int, name: str) -> None:
        if not isinstance(nb, int) or nb <= 0:
            raise Exception(f"[MultiView] the '{name}' must be a positive integer")
