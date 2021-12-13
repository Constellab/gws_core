import os

from gws_core import BaseTestCase, ConfigParams, File, Settings, Text, TextView


class TestTextView(BaseTestCase):

    def test_text_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Text.import_from_path(File(path=file_path), ConfigParams())
        _view = TextView(table)

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
