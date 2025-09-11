
import json
import os
from typing import Any, AnyStr, List, Optional

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import IntParam
from gws_core.impl.view.audio_view import AudioView
from gws_core.impl.view.html_view import HTMLView
from gws_core.impl.view.iframe_view import IFrameView
from gws_core.impl.view.image_view import ImageView
from gws_core.impl.view.markdown_view import MarkdownView
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
                    style=TypingStyle.material_icon("description"))
class File(FSNode):
    """
    Resource that represents a file in the system.


    ## Technical notes:
    /!\ The class that extend file can only have a path and  file_store_id attributes. Other attributes will not be
    provided when creating the resource.
    """

    __default_extensions__: List[str] = []
    """
    Override to define the default extensions of the file
    When upoading a file, if the file extension matches this list, this type will be used as default
    """

    TEXT_VIEW_NB_LINES = 100
    PAGE_PARAM_NAME = 'line_number'

    def __init__(self, path: str = ""):
        """ Create a new File

        :param path: absolute path to the file, defaults to ""
        :type path: str, optional
        """
        super().__init__(path)

        if self.exists() and not FileHelper.is_file(self.path):
            raise ValueError(f"The path {self.path} is not a file")

    @property
    def dir(self):
        return FileHelper.get_dir(self.path)

    @property
    def extension(self):
        return FileHelper.get_extension(self.path)

    def is_json(self):
        return FileHelper.is_json(self.path)

    def is_csv(self):
        return FileHelper.is_csv(self.path)

    def is_csv_or_excel(self):
        return FileHelper.is_csv(self.path) or self.extension in ['xls', 'xlsx']

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

    def is_audio(self):
        return FileHelper.is_audio(self.path)

    def is_video(self):
        return FileHelper.is_video(self.path)

    @property
    def mime(self):
        return FileHelper.get_mime(self.path)

    def set_name(self, name: Optional[str]) -> None:
        """
        Format the name of the file to ensure it has the correct extension

        :param name: name of the file
        :type name: str
        :return: formatted name
        :rtype: str
        """
        if not name:
            name = FileHelper.get_name(self.path)

        extension = FileHelper.get_extension(name)
        if extension != self.extension:
            name += f".{self.extension}"
        super().set_name(name)

    def open(self, mode: str, encoding: str = None) -> Any:
        """
        Open the file

        :param mode: mode of the file
        :type mode: str
        :param encoding: encoding used to open the file. If none the encoding is automatically detected with charset-normalizer, defaults to None
        :type encoding: str, optional
        :return: _description_
        :rtype: Any
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

    def read_part(self, from_line: int = 0, to_line: int = 10,
                  encoding: str = None,
                  mode: str = 'r+t') -> str:
        """
        Read a part of the file

        :param from_line: start line, defaults to 0
        :type from_line: int, optional
        :param to_line: end line (excluded), defaults to 10
        :type to_line: int, optional
        :param encoding: encoding used to read the file. If none the encoding is automatically detected with charset-normalizer, defaults to None
        :type encoding: str, optional
        :param mode: mode of the file, defaults to 'r+t'
        :type mode: str, optional
        :return: _description_
        :rtype: str
        """
        text = ""
        with self.open(mode, encoding=encoding) as file:
            for index, line in enumerate(file):
                if index >= from_line and index < to_line:
                    text += line
                if index >= to_line:
                    break
        return text

    def read(self, size: int = -1, encoding: str = None,
             mode: str = 'r+t') -> AnyStr:
        """
        Read the file

        :param size: size of the file to read, defaults to -1
        :type size: int, optional
        :param encoding: encoding used to read the file. If none the encoding is automatically detected with charset-normalizer, defaults to None
        :type encoding: str, optional
        :param mode: mode of the file, defaults to 'r+t'
        :type mode: str, optional
        :return: _description_
        :rtype: AnyStr
        """

        with self.open(mode, encoding=encoding) as file:
            data = file.read(size)
        return data

    def write(self, data: str, encoding: str = None,
              mode: str = 'a+t'):
        """
        Write data to the file

        :param data: data to write
        :type data: str
        :param encoding: encoding used to write the file. If none the encoding is automatically detected with charset-normalizer, defaults to None
        :type encoding: str, optional
        :param mode: mode of the file, defaults to 'a+t'
        :type mode: str, optional
        """
        with self.open(mode, encoding=encoding) as fp:
            fp.write(data)

    def detect_file_encoding(self, default_encoding: str = 'utf-8') -> str:
        """
        Detect the encoding of the file using charset-normalizer

        :param default_encoding: default encoding to use if the encoding is not detected, defaults to 'utf-8'
        :type default_encoding: str, optional
        :return: _description_
        :rtype: str
        """
        return FileHelper.detect_file_encoding(self.path, default_encoding)

    @view(view_type=JSONView, human_name="View as JSON", short_description="View the complete resource as json")
    def view_as_json(self, params: ConfigParams) -> JSONView:
        self.check_if_exists()
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
          specs=ConfigSpecs({"line_number": IntParam(default_value=1, min_value=1, human_name="From line")}))
    def view_content_as_str(self, params: ConfigParams) -> SimpleTextView:
        self.check_if_exists()
        return self.get_view_by_lines(params.get('line_number'))

    @view(view_type=View, human_name="Default view", short_description="View the file with automatic view",
          default_view=True, specs=ConfigSpecs({"line_number": IntParam(default_value=1, min_value=1, human_name="From line")}))
    def default_view(self, params: ConfigParams) -> View:
        self.check_if_exists()
        return self.get_default_view(params.get('line_number'))

    def get_default_view(self, page: int = 1) -> View:
        """
        Get the default view of the file.

        :param page: page number, defaults to 1
        :type page: int, optional
        :return: the default view
        :rtype: View
        """
        if page is None:
            page = 1
        # specific extension
        if self.is_image():
            return ImageView.from_local_file(self.path)
        if self.is_audio():
            return AudioView.from_local_file(self.path)
        if self.extension == 'html':
            return HTMLView(self.read())
        if self.extension == 'pdf':
            return IFrameView.from_file_model_id(self.get_model_id(), self.name)
        if self.is_video():
            return IFrameView.from_file_model_id(self.get_model_id(), self.name)
        if self.extension == 'md':
            return MarkdownView(self.read())

        # if the file is not readable, don't open the file and return the main view
        if not self.is_readable():
            return TextView("This file is not readable, please import or download it to view it")

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

    def check_if_exists(self):
        if not self.exists():
            raise BadRequestException(
                f"File {self.name or self.get_base_name()} does not exist")

    def get_default_style(self) -> TypingStyle:
        icon = self.get_icon_from_extension()

        if icon:
            return TypingStyle.material_icon(icon, background_color=None)
        return super().get_default_style()

    def get_icon_from_extension(self) -> Optional[str]:
        extension = self.extension

        if not extension:
            return None

        extension = extension.lower()

        if extension in ['csv', 'xls', 'xlsx']:
            return 'csv_file_icon'
        if extension in ['jpeg', 'jpg', 'png', 'gif', 'svg']:
            return 'image'
        if extension in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'aiff', 'alac']:
            return 'audiotrack'
        if extension == 'txt':
            return 'txt_file_icon'
        if extension == 'pdf':
            return 'pdf_file_icon'
        if extension in ['doc', 'docx']:
            return 'docx_file_icon'
        if extension == 'json':
            return 'json_file_icon'
        if extension in ['ppt', 'pptx']:
            return 'pptx_file_icon'
        if extension == 'zip':
            return 'zip_file_icon'
        if extension == 'py':
            return 'py_file_icon'

        return None
