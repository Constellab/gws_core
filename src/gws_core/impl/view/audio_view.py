

from base64 import b64encode

from gws_core.config.config_params import ConfigParams
from gws_core.impl.file.file_helper import FileHelper
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class AudioView(View):

    _base_64_audio: bytes
    _mime_type: str

    _type: ViewType = ViewType.AUDIO
    _title: str = "Audio"

    def __init__(self, _base_64_audio: bytes, _mime_type: str):
        super().__init__()
        self._base_64_audio = _base_64_audio
        self._mime_type = _mime_type

    def data_to_dict(self, params: ConfigParams) -> dict:
        return {
            "base_64_audio": self._base_64_audio,
            "mime_type": self._mime_type
        }

    @staticmethod
    def from_local_file(file_path: str) -> 'AudioView':
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

        # convert the file to base64
        with open(file_path, "rb") as audio_file:
            encoded_string = b64encode(audio_file.read())

        return AudioView(encoded_string, FileHelper.get_mime(file_path))
