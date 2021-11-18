# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
from typing import Any, AnyStr, List

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...impl.file.file_helper import FileHelper
from ...impl.json.json_view import JSONView
from ...resource.any_view import AnyView
from ...resource.resource_decorator import resource_decorator
from ...resource.view import View
from ...resource.view_decorator import view
from ..text.view.text_view import TextView
from .fs_node import FSNode


@resource_decorator("File")
class File(FSNode):
    """
    File class.

    /!\ The class that extend file can only have a path and  file_store_uri attributes. Other attributes will not be
    provided when creating the resource
    """

    _mode = "t"

    # Override this attribute to define the list of file extension the class supports
    supported_extensions: List[str] = []

    @property
    def size(self):
        return FileHelper.get_size(self.path)

    @property
    def dir(self):
        return FileHelper.get_dir(self.path)

    @property
    def extension(self):
        return FileHelper.get_extension(self.path)

    def is_large(self):
        return FileHelper.is_large(self.path)

    def is_json(self):
        return FileHelper.is_json(self.path)

    def is_csv(self):
        return FileHelper.is_csv(self.path)

    def is_txt(self):
        return FileHelper.is_txt(self.path)

    def is_jpg(self):
        return FileHelper.is_jpg(self.path)

    def is_png(self):
        return FileHelper.is_png(self.path)

    @property
    def mime(self):
        return FileHelper.get_mime(self.path)

    @property
    def name(self):
        return FileHelper.get_name_with_extension(self.path)

    def get_name(self) -> str:
        return self.name

    # -- O --

    def open(self, mode: str):
        """
        Open the file
        """

        if self._exists():
            return open(self.path, mode, encoding='utf-8')
        else:
            if not os.path.exists(self.dir):
                os.makedirs(self.dir)
                if not os.path.exists(self.dir):
                    raise BadRequestException(f"Cannot create directory {self.dir}")
            return open(self.path, mode="w+", encoding='utf-8')

    def read_part(self, from_line: int = 1, to_line: int = 10) -> AnyStr:
        text = ""
        mode = "r+"+self._mode
        with self.open(mode) as fp:
            for index, line in enumerate(fp):
                if index >= from_line-1 and index <= to_line-1:
                    text += line
                if to_line > to_line-1:
                    break
        return text

    def _read_all(self, size: int = -1) -> AnyStr:
        mode = "r+"+self._mode
        with self.open(mode) as fp:
            data = fp.read(size)
        return data

    def read(self, size: int = -1) -> AnyStr:
        if self.is_large() and size == -1:
            return self.read_part()
        else:
            return self._read_all(size=-1)

    # def readline(self) -> AnyStr:
    #     mode = "r+"+self._mode
    #     with self.open(mode) as file:
    #         data = file.readline()
    #     return data

    # def readlines(self, hint=-1) -> List[AnyStr]:
    #     mode = "r+"+self._mode
    #     with self.open(mode) as file:
    #         data = file.readlines(hint)
    #     return data

    @view(view_type=JSONView, human_name="View as JSON", short_description="View the complete resource as json")
    def view_as_json(self, params: ConfigParams) -> JSONView:
        content = self.read()
        try:
            json_: Any = json.loads(content)
            return JSONView(json_)
        except:
            pass

        # rollback to string view if not convertible to json
        return self.view_content_as_str(params)

    @view(view_type=View, human_name="View file content", short_description="View the file content as string")
    def view_content_as_str(self, params: ConfigParams) -> TextView:
        content = self.read()
        return TextView(content)

    @view(view_type=View, human_name="Default view", short_description="View the file with automatic view", default_view=True)
    def default_view(self, params: ConfigParams) -> View:
        content = self.read()

        if self.is_json():
            try:
                # try to load the json
                json_: Any = json.loads(content)

                # If the json, is a json of a view
                if View.json_is_from_view(json_):
                    return AnyView(json_)

                # return content as json
                return JSONView(json_)
            except:
                pass

        # In the worse case, return the file content as string
        return TextView(content)

    def write(self, data: str):
        """
        Write in the file
        """
        mode = "a+"+self._mode
        with self.open(mode) as fp:
            fp.write(data)

