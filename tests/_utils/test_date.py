

from datetime import datetime
from email.headerregistry import DateHeader
from unittest import IsolatedAsyncioTestCase

from gws_core.core.utils.date_helper import DateHelper
from gws_core.test.base_test_case import BaseTestCase


class TestDate(IsolatedAsyncioTestCase):

    def test_convert_to_utc(self):

        date: datetime = datetime.fromisoformat('2022-01-27T14:11:39.569+03:00')
        date2: datetime = DateHelper.convert_datetime_to_utc(date)

        self.assertEqual(date2.isoformat(), '2022-01-27T11:11:39.569000+00:00')

        date = datetime.fromisoformat('2022-01-27T14:11:39.569')
        date2 = DateHelper.convert_datetime_to_utc(date)

        self.assertEqual(date2.isoformat(), '2022-01-27T14:11:39.569000+00:00')
