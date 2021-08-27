# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Union

from ..core.classes.paginator import Paginator
from ..core.service.base_service import BaseService
from .system import Monitor


class LabService(BaseService):

    @classmethod
    def get_lab_monitor_data(cls,
                             page: int = 0,
                             number_of_items_per_page: int = 20,
                             as_json: bool = False) -> Union[Paginator, dict]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        query = Monitor.select()
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json()
        else:
            return paginator
