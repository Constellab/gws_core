import os

from gws_core import BaseTestCase, Settings, Text, TextView


class TestTextView(BaseTestCase):

    def test_text_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Text.import_from_path(file_path)
        vw = TextView(table)

        self.assertEqual(
            len(vw._slice(from_char_index=10, to_char_index=400)),
            390
        )

        self.assertEqual(
            len(vw._slice(from_char_index=10, to_char_index=400000)),
            3965
        )

        self.assertEqual(
            len(vw.to_dict(page=2, page_size=100)["data"]),
            100
        )
