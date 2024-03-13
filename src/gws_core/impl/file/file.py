
import json
import os
from typing import Any, AnyStr, List

from gws_core.config.param.param_spec import IntParam
from gws_core.impl.view.html_view import HTMLView
from gws_core.impl.view.image_view import ImageView
from gws_core.model.typing_style import TypingStyle

from ...config.config_params import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...impl.file.file_helper import FileHelper
from ...impl.json.json_view import JSONView
from ...resource.resource_decorator import resource_decorator
from ...resource.view.any_view import AnyView
from ...resource.view.view import View
from ...resource.view.view_decorator import view
from ..text.text_view import SimpleTextView, TextView, TextViewData
from .fs_node import FSNode


@resource_decorator("File", human_name="File",
                    style=TypingStyle.material_icon("description", background_color="#346b02"))
class File(FSNode):
    """
    File class.

    /!\ The class that extend file can only have a path and  file_store_id attributes. Other attributes will not be
    provided when creating the resource
    """

    _mode = "t"

    """
    Override to define the default extensions of the file
    When upoading a file, if the file extension matches this list, this type will be used as default
    """
    __default_extensions__: List[str] = []

    TEXT_VIEW_NB_LINES = 100
    PAGE_PARAM_NAME = 'line_number'

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

    def is_image(self):
        return FileHelper.is_image(self.path)

    def is_empty(self) -> bool:
        return self.get_size() == 0

    def is_readable(self) -> bool:
        return self.extension not in [
            "exe", "dll", "so", "pyc", "pyo", "xlsx", "xls", "doc", "docx", "pdf", "zip", "gz"]

    @property
    def mime(self):
        return FileHelper.get_mime(self.path)

    def copy_to_path(self, destination: str) -> str:
        """
        Copy the file to the target path
        """
        FileHelper.copy_file(self.path, destination)
        return destination

    def get_base_name(self) -> str:
        return FileHelper.get_name_with_extension(self.path)

    def open(self, mode: str, encoding: str = None) -> Any:
        """
        Open the file
        """

        if encoding is None:
            encoding = self.detect_file_encoding()

        if self.exists():
            return open(self.path, mode, encoding=encoding)
        else:
            if not os.path.exists(self.dir):
                os.makedirs(self.dir)
                if not os.path.exists(self.dir):
                    raise BadRequestException(
                        f"Cannot create directory {self.dir}")
            return open(self.path, mode="w+", encoding=encoding)

    def read_part(self, from_line: int = 0, to_line: int = 10) -> str:
        text = ""
        mode = "r+" + self._mode
        with self.open(mode) as file:
            for index, line in enumerate(file):
                if index >= from_line and index < to_line:
                    text += line
                if index >= to_line:
                    break
        return text

    def read(self, size: int = -1) -> AnyStr:
        mode = "r+"+self._mode
        with self.open(mode) as file:
            data = file.read(size)
        return data

    def detect_file_encoding(self, default_encoding: str = 'utf-8') -> str:
        return FileHelper.detect_file_encoding(self.path, default_encoding)

    @view(view_type=JSONView, human_name="View as JSON", short_description="View the complete resource as json")
    def view_as_json(self, params: ConfigParams) -> JSONView:
        # if the file is not readable,don't open the file and return the main view
        if not self.is_readable():
            return super().view_as_json(ConfigParams())

        content = self.read()
        try:
            json_: Any = json.loads(content)
            return JSONView(json_)
        except:
            pass

        # rollback to string view if not convertible to json
        return self.view_content_as_str(params)

    @view(view_type=SimpleTextView, human_name="View file content", short_description="View the file content as string",
          specs={"line_number": IntParam(default_value=1, min_value=1, human_name="From line")})
    def view_content_as_str(self, params: ConfigParams) -> SimpleTextView:
        return self.get_view_by_lines(params.get('line_number'))

    @view(view_type=View, human_name="Default view", short_description="View the file with automatic view",
          default_view=True, specs={"line_number": IntParam(default_value=1, min_value=1, human_name="From line")})
    def default_view(self, params: ConfigParams) -> View:
        return self.get_default_view(params.get('line_number'))

    def get_default_view(self, page: int = 1) -> View:
        if page is None:
            page = 1
        # specific extension
        if self.is_image():
            return ImageView.from_local_file(self.path)
        if self.extension == 'html':
            return HTMLView(self.read())

        # if the file is not readable, don't open the file and return the main view
        if not self.is_readable():
            return TextView("This file is not readable, please import it to view it")

        if self.is_json():
            try:
                # try to load the json
                json_: Any = json.loads(self.read())

                # If the json, is a json of a view
                if View.json_is_from_view(json_):
                    return AnyView(json_)

                # return content as json
                return JSONView(json_)
            except:
                pass

        # In the worse case, return the file content as string
        return self.get_view_by_lines(page)

    def get_view_by_lines(self, start_line: int = 1) -> SimpleTextView:
        end_line = start_line + self.TEXT_VIEW_NB_LINES - 1
        text = self.read_part(start_line - 1, end_line)
        lines_count = len(text.splitlines())
        return SimpleTextView(TextViewData(
            text=text,
            is_first_page=start_line <= 1,
            is_last_page=lines_count < self.TEXT_VIEW_NB_LINES,
            next_page=start_line + self.TEXT_VIEW_NB_LINES,
            previous_page=max(start_line - self.TEXT_VIEW_NB_LINES, 1),
            page_param_name=self.PAGE_PARAM_NAME
        ))

    def write(self, data: str):
        """
        Write in the file
        """
        mode = "a+"+self._mode
        with self.open(mode) as fp:
            fp.write(data)
