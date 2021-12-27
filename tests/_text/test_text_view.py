
from gws_core import BaseTestCase, ConfigParams, TextView, ViewTester
from gws_core.extra import DataProvider
from gws_core.impl.text.text import Text
from gws_core.impl.text.text_tasks import TextImporter


class TestTextView(BaseTestCase):

    async def test_text_view(self,):
        text: Text = TextImporter.call(DataProvider.get_iris_file())

        tester = ViewTester(
            view=TextView(text)
        )
        dic = tester.to_dict(
            {"page": 2, "page_size": 1000}
        )

        self.assertEqual(dic["data"]["total_number_of_pages"], 4)
