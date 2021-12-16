
from gws_core import BaseTestCase, ConfigParams, TextView
from gws_core.impl.text.text import Text
from gws_core.impl.text.text_tasks import TextImporter
from tests.gws_core_test_helper import GwsCoreTestHelper


class TestTextView(BaseTestCase):

    async def test_text_view(self,):
        text: Text = TextImporter.call(GwsCoreTestHelper.get_iris_file())
        _view = TextView(text)

        self.assertEqual(
            len(_view._slice(from_char_index=10, to_char_index=400)),
            390
        )

        self.assertEqual(
            len(_view._slice(from_char_index=10, to_char_index=400000)),
            3965
        )

        params = ConfigParams(
            {"page": 2, "page_size": 100}
        )
        self.assertEqual(
            len(_view.to_dict(params)["data"]),
            10
        )
