

from datetime import date, datetime, timedelta, timezone


class DateHelper:

    @staticmethod
    def convert_datetime_to_utc(datetime_: datetime) -> datetime:
        return datetime_.astimezone()

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def now_utc_as_milliseconds() -> int:
        return int(DateHelper.now_utc().timestamp() * 1000)

    @staticmethod
    def from_str(date_str: str, format: str) -> datetime:
        return datetime.strptime(date_str, format)

    @staticmethod
    def from_iso_str(date_str: str) -> datetime:
        return datetime.fromisoformat(date_str)

    @staticmethod
    def to_iso_str(date: datetime) -> str:
        return date.isoformat()

    @staticmethod
    def to_rfc7231_str(date: datetime) -> str:
        """convert a datetime to a string in the RFC 7231 format. Useful for HTTP headers.
        """
        return date.strftime('%a, %d %b %Y %H:%M:%S GMT')

    @staticmethod
    def are_same_day(date1: datetime, date2: datetime) -> bool:
        return date1.date() == date2.date()

    @staticmethod
    def date_range(start_date: date, end_date: date, include_end_date: bool = False):
        """This method is usefule to iterate over a range of dates.
        One iteration is one day.
        """
        if include_end_date:
            end_date += timedelta(days=1)

        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    @staticmethod
    def get_duration_pretty_text(duration_in_seconds: float) -> str:
        """Return a string representing the duration in a human readable way.
        """
        duration_in_seconds = abs(duration_in_seconds)
        if duration_in_seconds < 60:
            return f'{duration_in_seconds:.0f} secs'

        duration_in_minutes = duration_in_seconds // 60
        if duration_in_minutes < 60:
            rest_in_seconds = duration_in_seconds % 60
            if rest_in_seconds > 0:
                return f'{duration_in_minutes:.0f} mins, {rest_in_seconds:.0f} secs'
            return f'{duration_in_minutes:.0f} mins'

        duration_in_hours = duration_in_minutes / 60
        if duration_in_hours < 24:
            rest_in_minutes = duration_in_minutes % 60
            if rest_in_minutes > 0:
                return f'{duration_in_hours:.0f} hours, {rest_in_minutes:.0f} mins'
            return f'{duration_in_hours:.0f} hours'

        duration_in_days = duration_in_hours / 24
        rest_in_hours = duration_in_hours % 24
        if rest_in_hours > 0:
            return f'{duration_in_days:.0f} days, {rest_in_hours:.0f} hours'
        return f'{duration_in_days:.0f} days'
