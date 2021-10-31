# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from ...config.config_types import ConfigParams
from ...config.param_spec import StrParam
from ...core.exception.exceptions import BadRequestException
from ...impl.file.file import File
from ...resource.r_field import RField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from ...task.exporter import export_to_path
from ...task.importer import import_from_path
from .view.text_view import TextView


@resource_decorator("Text")
class Text(Resource):
    _data: str = RField()

    def __init__(self, data: str):
        super().__init__()
        self._set_data(data)
        
    def _set_data(self, data: str) -> 'Text':
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

    @export_to_path(specs={
        'file_name': StrParam(default_value='file.txt', short_description="Destination file name in the store"),
        'encoding': StrParam(default_value='utf-8', short_description="Text encoding"),
        'file_store_uri': StrParam(optional=True, short_description="URI of the file_store where the file must be exported"),
    })
    def export_to_path(self, dir_: str, params: ConfigParams) -> File:
        """
        Export to a repository

        :param file_path: The destination file path
        :type file_path: File
        """
        file_path = os.path.join(dir_, params.get_value('file_name', 'file.txt'))

        try:
            with open(file_path, 'w+t', encoding=params.get_value('encoding', 'utf-8')) as fp:
                fp.write(self._data)
        except Exception as err:
            raise BadRequestException("Cannot export the text") from err

        return File(file_path)

    # -- I --

    @classmethod
    @import_from_path(specs={'encoding': StrParam(default_value='utf-8', short_description="Text encoding")})
    def import_from_path(cls, file: File, params: ConfigParams) -> 'Text':
        """
        Import from a repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        try:
            with open(file.path, 'r+t', encoding=params.get_value('encoding', 'utf-8')) as fp:
                text = fp.read()
        except Exception as err:
            raise BadRequestException("Cannot import the text") from err

        return cls(data=text)

    @view(view_type=TextView, human_name='Text', short_description='View as text',
          specs={})
    def view_as_text(self, params: ConfigParams) -> TextView:
        """
        View as table
        """

        return TextView(self._data)
