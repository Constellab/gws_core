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
