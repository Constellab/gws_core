# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import os
from base64 import b64encode
from unittest import TestCase

from gws_core import ImageView, Settings
from gws_core.config.config_types import ConfigParams


# test_image_view
class TestImageView(TestCase):

    def test_image_view(self):

        temp_dir = Settings.get_instance().make_temp_dir()

        # Create a file
        file_path = os.path.join(temp_dir, "test_image.png")

        content = b"test"
        encoded_context = b64encode(content)

        with open(file_path, "wb") as f:
            f.write(content)

        # Create an ImageView from the file
        view = ImageView.from_local_file(file_path)

        # Check the dict
        dic = view.to_dict(ConfigParams())
        self.assertEqual(dic["type"], "image-view")
        self.assertEqual(dic["data"]["base_64_img"], encoded_context)
        self.assertEqual(dic["data"]["mime_type"], "image/png")
