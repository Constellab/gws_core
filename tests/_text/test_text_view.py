# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, TextView, ViewTester
from gws_core.extra import DataProvider
from gws_core.impl.text.text import Text
from gws_core.impl.text.text_tasks import TextImporter


class TestTextView(BaseTestCase):

    def test_text_view(self,):
        text: Text = TextImporter.call(DataProvider.get_iris_file())

        tester = ViewTester(
            view=TextView(text)
        )
        dic = tester.to_dict(
            {"page": 2, "page_size": 1000}
        )

        self.assertEqual(dic["data"]["total_number_of_pages"], 4)
