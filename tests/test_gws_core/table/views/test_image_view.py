from unittest import TestCase

from gws_core import ImageView
from gws_core.config.config_params import ConfigParams
from gws_core.resource.view.view_types import ViewType


# test_image_view
class TestImageView(TestCase):
    def test_image_view(self):
        # Create an ImageView with a URL source
        view = ImageView(src="http://localhost/api/fs-node/123/resource/abc/preview/test.png")

        # Check the dict
        view_dto = view.to_dto(ConfigParams())
        self.assertEqual(view_dto.type, ViewType.IMAGE)
        self.assertEqual(view_dto.data["src"], "http://localhost/api/fs-node/123/resource/abc/preview/test.png")
