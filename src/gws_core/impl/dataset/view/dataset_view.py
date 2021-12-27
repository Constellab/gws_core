# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from gws_core.config.config_types import ConfigParams
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException
from ...table.view.table_view import TableView

if TYPE_CHECKING:
    from ..dataset import Dataset


class DatasetView(TableView):
    """
    Class table view.

    The view model is:
    ```
    {
        "type": "dataset-view",
        "data": dict,
        "from_row": int,
        "number_of_rows_per_page": int,
        "from_column": int,
        "number_of_columns_per_page": int,
        "total_number_of_rows": int,
        "total_number_of_columns": int,
        "target_names": List[str],
    }
    ```
    """

    _type = "dataset-view"
    _data: Dataset

    def _check_and_set_data(self, data: Dataset):
        from ..dataset import Dataset
        if not isinstance(data, Dataset):
            raise BadRequestException("The data must be a pandas.DataFrame or Table resource")
        super()._check_and_set_data(data)

    def to_dict(self, params: ConfigParams) -> dict:
        dict_ = super().to_dict(params)
        dict_["target_names"] = self._data.target_names
        return dict_
