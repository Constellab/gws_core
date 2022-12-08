# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime, timezone


class DateHelper:

    @staticmethod
    def convert_datetime_to_utc(datetime_: datetime) -> datetime:
        return datetime_.astimezone()

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def now_utc_as_milliseconds() -> datetime:
        return int(DateHelper.now_utc().timestamp() * 1000)

    @staticmethod
    def from_str(date_str: str, format: str) -> datetime:
        return datetime.strptime(date_str, format)

    @staticmethod
    def from_iso_str(date_str: str) -> datetime:
        return datetime.fromisoformat(date_str)

    @staticmethod
    def are_same_day(date1: datetime, date2: datetime) -> bool:
        return date1.date() == date2.date()
