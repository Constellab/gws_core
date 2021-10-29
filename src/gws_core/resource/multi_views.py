

from typing import Any, Dict, List

from .view import View


class MultiViews(View):
    """Class MultiView. This is use to multiple view in the same page

    The view model is:
    ```
    {
        "type": "multi-view"
        "data": list[{
          "view_dict": {},
          "colspan": colspan,
          "rowspan": rowspan,
        }],
    }
    ```
    """

    _views_dict: List[dict]
    _type = "multi-view"
    _nb_of_columns: int

    def __init__(self, nb_of_columns: int, *args, **kwargs):
        """[summary]

        :param nb_of_columns: total number of columns of the grid
        :type nb_of_columns: int
        """
        super().__init__(None, *args, **kwargs)
        self._check_number(nb_of_columns, 'Number of columns')
        self._views_dict = []
        self._nb_of_columns = nb_of_columns

    def add_view(self, view_dict: Dict[str, Any], colspan: int = 1, rowspan: int = 1) -> None:
        """Add a view to the multi view

        :param view_dict: dict of a view. Dictionary of a view from to_dict method
        :type view_dict: Dict[str, Any]
        :param colspan: Nb of columns taken by the view in the grid, defaults to 1
        :type colspan: int, optional
        :param rowspan: Nb of rows taken by the view in the grid, defaults to 1
        :type rowspan: int, optional
        :raises Exception: [description]
        """

        if not self.json_is_from_view(view_dict):
            raise Exception('[MultiViews] the povided dictionary if not a view dictionary')

        self._check_number(colspan, 'Colums span')
        self._check_number(rowspan, 'Rows span')

        if colspan > self._nb_of_columns:
            raise Exception('[MultiViews] the colums span must not be bigger than the number of columns')

        self._views_dict.append(
            {
                "view": view_dict,
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
        self._views_dict.append(
            {
                "view": {"type": "empty-view"},
                "colspan": colspan,
                "rowspan": rowspan,
            }
        )

    def to_dict(self, *args, **kwargs) -> dict:
        return {
            "type": self._type,
            "nb_of_columns": self._nb_of_columns,
            "data": self._views_dict
        }

    def _check_number(self, nb: int, name: str) -> None:
        if not isinstance(nb, int) or nb <= 0:
            raise Exception(f"[MultiView] the '{name}' must be a positive integer")
