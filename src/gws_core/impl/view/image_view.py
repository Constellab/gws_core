

from base64 import b64encode

from gws_core.config.config_params import ConfigParams
from gws_core.impl.file.file_helper import FileHelper
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class ImageView(View):
    """Image view.

    Use static method from_local_file to create an ImageView from a local file.

    :param base_64_img: The base 64 encoded image
    :type base_64_img: bytes
    :param _mime_type: The mime type of the image
    :type _mime_type: str

    """

    _base_64_img: bytes = None
    _mime_type: str

    _type: ViewType = ViewType.IMAGE
    _title: str = "Image"

    def __init__(self, base_64_img: bytes, _mime_type: str):
        super().__init__()
        self._base_64_img = base_64_img
        self._mime_type = _mime_type

    def data_to_dict(self, params: ConfigParams) -> dict:
        return {
            "base_64_img": self._base_64_img,
            "mime_type": self._mime_type
        }

    @staticmethod
    def from_local_file(file_path: str) -> 'ImageView':
        """Create an ImageView from a local file path

        :param file_path: The path of the file
        :type file_path: str
        :return: The ImageView
        :rtype: ImageView
        """
        if not FileHelper.exists_on_os(file_path):
            raise Exception(f"The file '{file_path}' does not exist")

        if not FileHelper.is_file(file_path):
            raise Exception(f"The path '{file_path}' is not a file")

        with open(file_path, "rb") as image_file:
            encoded_string = b64encode(image_file.read())
        return ImageView(encoded_string, FileHelper.get_mime(file_path))
