# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.resource.r_field.primitive_r_field import StrRField

from ...config.config_params import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view.view_decorator import view
from .view.text_view import TextView


@resource_decorator("Text")
class Text(Resource):
    DEFAULT_FILE_FORMAT = "txt"
    _data: str = StrRField(searchable=False)

    def __init__(self, data: str = None):
        super().__init__()
        self.set_data(data)

    def set_data(self, data: str) -> None:
        if data is None:
            data = ""

        if not isinstance(data, str):
            raise BadRequestException(
                "The data must be a string")
        self._data = data

    def get_data(self) -> str:
        return self._data

    @view(view_type=TextView, human_name='Text', short_description='View as text',
          specs={}, default_view=True)
    def view_as_text(self, params: ConfigParams) -> TextView:
        """
        View as table
        """

        return TextView(self._data)
