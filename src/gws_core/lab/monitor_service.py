# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ..core.classes.paginator import Paginator
from ..core.service.base_service import BaseService
from .monitor import Monitor


class MonitorService(BaseService):

    @classmethod
    def get_lab_monitor_data(cls,
                             page: int = 0,
                             number_of_items_per_page: int = 20) -> Paginator:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        query = Monitor.select()
        return Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)
