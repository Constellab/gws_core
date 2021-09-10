# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ..core.service.base_service import BaseService
from .progress_bar import ProgressBar


class ProgressBarService(BaseService):

    @classmethod
    def fetch_progress_bar(cls, uri: str) -> ProgressBar:
        return ProgressBar.get_by_uri_and_check(uri)
