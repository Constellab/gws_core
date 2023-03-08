# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from datetime import datetime
from typing import List, Optional, TypedDict

from ..core.service.base_service import BaseService
from .progress_bar import ProgressBar, ProgressBarMessage


class ProgressBarMessagesDTO(TypedDict):
    from_datatime: Optional[datetime]
    to_datatime: Optional[datetime]
    messages: List[ProgressBarMessage]


class ProgressBarService(BaseService):

    @classmethod
    def download_progress_bar(cls, id: str) -> str:
        progress_bar: ProgressBar = ProgressBar.get_by_id_and_check(id)
        return progress_bar.get_messages_as_str()

    @classmethod
    def get_progress_bar_messages(
            cls, id: str, nb_of_messages: int, from_datetime: datetime = None) -> ProgressBarMessagesDTO:
        progress_bar: ProgressBar = ProgressBar.get_by_id_and_check(id)

        messages = progress_bar.get_messages_paginated(nb_of_messages=20, before_date=from_datetime)

        return {
            'from_datatime': messages[-1]['datetime'] if messages else None,
            'to_datatime': messages[0]['datetime'] if messages else None,
            'messages': progress_bar.get_messages_paginated(nb_of_messages=nb_of_messages, before_date=from_datetime)
        }
