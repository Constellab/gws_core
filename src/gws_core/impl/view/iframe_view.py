from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.settings import Settings
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class IFrameView(View):
    """
    Class iframe view.

    The view model is:
    ```
    {
        "type": "iframe-view"
        "data": {'src': str}
    }
    ```
    """

    _type: ViewType = ViewType.IFRAME
    _src: str

    def __init__(self, src: str = None):
        super().__init__()
        self._src = src

    def data_to_dict(self, params: ConfigParams = None) -> dict:
        return {"src": self._src}

    @staticmethod
    def from_file_model_id(file_model_id: str, file_name: str, resource_uid: str) -> "IFrameView":
        """Create an IFrameView from a file model id.
        We use the filename and resource uid to ensure the link is valid, because this route is public.


        :param file_model_id: The file model id
        :type file_model_id: str
        :param file_name: The file name
        :type file_name: str
        :param resource_uid: The resource uid
        :type resource_uid: str
        :return: The IFrameView
        :rtype: IFrameView
        """
        url = f"{Settings.get_lab_api_url()}/{Settings.core_api_route_path()}/fs-node/{file_model_id}/resource/{resource_uid}/preview/{file_name}"
        return IFrameView(url)
