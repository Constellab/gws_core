# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import date, datetime
from unittest import IsolatedAsyncioTestCase

from gws_core.core.utils.date_helper import DateHelper


# test_date
class TestDate(IsolatedAsyncioTestCase):

    def test_convert_to_utc(self):

        date: datetime = datetime.fromisoformat('2022-01-27T14:11:39.569+03:00')
        date2: datetime = DateHelper.convert_datetime_to_utc(date)

        self.assertEqual(date2.isoformat(), '2022-01-27T11:11:39.569000+00:00')

        date = datetime.fromisoformat('2022-01-27T14:11:39.569')
        date2 = DateHelper.convert_datetime_to_utc(date)

        self.assertEqual(date2.isoformat(), '2022-01-27T14:11:39.569000+00:00')

    def test_daterange(self):

        start_date = date(2013, 1, 1)
        end_date = date(2013, 1, 10)

        count = 0
        for _ in DateHelper.date_range(start_date, end_date, True):
            count += 1

        self.assertEqual(count, 10)
