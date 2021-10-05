# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...config.param_spec import IntParam, StrParam
from ...core.exception.exceptions import BadRequestException
from ...resource.r_field import RField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from .view.text_view import TextView


@resource_decorator("Text")
class Text(Resource):
    _data: str = RField()

    def set_data(self, data: str):
        if isinstance(data, str):
            raise BadRequestException(
                "The data must be a string")
        self._data = data

    def get_data(self):
        return self._data

    @view(view_type=TextView, human_name='Text', short_description='View as text',
          specs={
              "page": IntParam(default_value=1, min_value=0, human_name="Page to view"),
              "number_of_chars_per_page": IntParam(default_value=3000, min_value=1, max_value=3000, human_name="Number of chars per page"),
              "title": StrParam(default_value="", human_name="Title", description="The table title"),
              "subtitle": StrParam(default_value="", human_name="Subtitle", description="The table subtitle")
          })
    def view_as_text(self, *args, **kwargs) -> dict:
        """
        View as table
        """

        vw = TextView(self._data)
        return vw.to_dict(*args, **kwargs)
