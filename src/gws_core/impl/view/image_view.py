from urllib.parse import quote

from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.settings import Settings
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class ImageView(View):
    """Image view.

    Serves the image via a URL route, avoiding large base64 payloads.
    Use ``from_file_model_id`` to create an instance.
    """

    _src: str

    _type: ViewType = ViewType.IMAGE
    _title: str = "Image"

    def __init__(self, src: str):
        super().__init__()
        self._src = src

    def data_to_dict(self, params: ConfigParams) -> dict:
        return {"src": self._src}

    UNSUPPORTED_EXTENSIONS = ["tiff", "tif"]

    @staticmethod
    def from_file_model_id(
        file_model_id: str, file_name: str, resource_model_id: str
    ) -> "ImageView":
        """Create an ImageView that serves the image via a URL route.

        Uses the same preview route as IFrameView.

        :param file_model_id: The file model id
        :type file_model_id: str
        :param file_name: The file name
        :type file_name: str
        :param resource_model_id: The resource model id
        :type resource_model_id: str
        :return: The ImageView
        :rtype: ImageView
        :raises Exception: If the image format is not supported by browsers
        """
        extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        if extension in ImageView.UNSUPPORTED_EXTENSIONS:
            raise Exception(
                f"Image format '{extension}' is not supported for browser display. "
                "Please convert the image to a supported format (e.g., PNG, JPEG)."
            )

        base_url = Settings.get_lab_api_url().rstrip("/")
        api_route = Settings.core_api_route_path().strip("/")
        encoded_file_name = quote(file_name, safe="")
        url = f"{base_url}/{api_route}/fs-node/{file_model_id}/resource/{resource_model_id}/preview/{encoded_file_name}"
        return ImageView(src=url)
