from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from pandas import DataFrame

from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....resource.view import View

if TYPE_CHECKING:
    from ..table import Table


class BaseTableView(View):
    _type: str
    _data: DataFrame

    def __init__(self, data: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._check_and_set_data(data)

    def _check_and_set_data(self, data: Union[DataFrame, Table]):
        from ..table import Table
        if not isinstance(data, (DataFrame, Table,)):
            raise BadRequestException("The data must be a pandas.DataFrame or Table resource")
        if isinstance(data, Table):
            data = data.get_data()
        self._data = data
