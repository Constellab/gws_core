# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ..core.service.base_service import BaseService
from .progress_bar import ProgressBar


class ProgressBarService(BaseService):

    @classmethod
    def fetch_progress_bar(cls, id: str) -> ProgressBar:
        return ProgressBar.get_by_id_and_check(id)

    @classmethod
    def download_progress_bar(cls, id: str) -> str:
        progress_bar: ProgressBar = ProgressBar.get_by_id_and_check(id)
        return progress_bar.get_messages_as_str()
