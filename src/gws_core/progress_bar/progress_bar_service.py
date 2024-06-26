

from datetime import datetime

from gws_core.progress_bar.progress_bar_dto import \
    ProgressBarMessagesBetweenDatesDTO

from .progress_bar import ProgressBar


class ProgressBarService():

    @classmethod
    def download_progress_bar(cls, id: str) -> str:
        progress_bar: ProgressBar = ProgressBar.get_by_id_and_check(id)
        return progress_bar.get_messages_as_str()

    @classmethod
    def get_progress_bar_messages(
            cls, id: str, nb_of_messages: int, from_datetime: datetime = None) -> ProgressBarMessagesBetweenDatesDTO:
        progress_bar: ProgressBar = ProgressBar.get_by_id_and_check(id)

        messages = progress_bar.get_messages_paginated(nb_of_messages=20, before_date=from_datetime)

        return ProgressBarMessagesBetweenDatesDTO(
            from_datatime=messages[-1].datetime if messages else None,
            to_datatime=messages[0].datetime if messages else None,
            messages=progress_bar.get_messages_paginated(nb_of_messages=nb_of_messages, before_date=from_datetime)
        )
