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

    def set_data(self, data: str) -> 'Text':
        if data is None:
            data = ""

        if not isinstance(data, str):
            raise BadRequestException(
                "The data must be a string")
        self._data = data
        return self

    def get_data(self):
        return self._data

    # -- E --

    def export_to_path(self, file_path: str, encoding="utf-8", **kwargs):
        """
        Export to a repository

        :param file_path: The destination file path
        :type file_path: File
        """

        try:
            with open(file_path, 'w+t', encoding=encoding) as fp:
                fp.write(self._data)
        except Exception as err:
            raise BadRequestException("Cannot export the text") from err

    # -- I --

    @classmethod
    def import_from_path(cls, file_path: str, encoding="utf-8", **kwargs) -> 'Text':
        """
        Import from a repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        try:
            with open(file_path, 'r+t', encoding=encoding) as fp:
                text = fp.read()
        except Exception as err:
            raise BadRequestException("Cannot import the text") from err

        return cls().set_data(data=text)

    @ view(view_type=TextView, human_name='Text', short_description='View as text',
           specs={
               "page": IntParam(default_value=1, min_value=0, human_name="Page to view"),
               "number_of_chars_per_page": IntParam(default_value=3000, min_value=1, max_value=3000, human_name="Number of chars per page"),
               "title": StrParam(default_value="", human_name="Title", short_description="The table title"),
               "subtitle": StrParam(default_value="", human_name="Subtitle", short_description="The table subtitle")
           })
    def view_as_text(self, *args, **kwargs) -> dict:
        """
        View as table
        """

        vw = TextView(self._data)
        return vw.to_dict(*args, **kwargs)
