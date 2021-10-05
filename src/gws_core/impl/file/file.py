# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import Any, AnyStr, List, Type, final

from ...core.exception.exceptions import BadRequestException
from ...impl.file.file_helper import FileHelper
from ...impl.json.json_view import JsonView
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.resource_set import ResourceSet
from ...resource.view_decorator import view
from ..text.view.text_view import TextView


@final
@resource_decorator("File")
class File(Resource):
    """
    File class
    """

    path: str = ""
    file_store_uri: str = ""
    _mode = "t"

    @property
    def dir(self):
        return FileHelper.get_dir(self.path)

    # -- E --

    @property
    def extension(self):
        return FileHelper.get_extension(self.path)

    def _exists(self):
        return os.path.exists(self.path)

    # -- F --

    # -- I --

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

    # -- M --

    @property
    def mime(self):
        return FileHelper.get_mime(self.path)

    @property
    def name(self):
        return FileHelper.get_name_with_extension(self.path)

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

    # -- R --

    def read(self) -> AnyStr:
        mode = "r+"+self._mode
        with self.open(mode) as fp:
            data = fp.read()
        return data

    def readline(self) -> AnyStr:
        mode = "r+"+self._mode
        with self.open(mode) as fp:
            data = fp.readline()
        return data

    def readlines(self, n=-1) -> List[AnyStr]:
        mode = "r+"+self._mode
        with self.open(mode) as fp:
            data = fp.readlines(n)
        return data

    # -- T --

    @view(human_name="View as JSON", short_description="View the complete resource as json")
    def view_as_dict(self) -> dict:
        _json = super().view_as_dict()
        _json["path"] = self.path
        _json["content"] = self.read()
        return JsonView(_json).to_dict()

    @view(human_name="View file content", short_description="View the file content as string", default_view=True)
    def view_content_as_str(self) -> dict:
        content = self.read()

        return TextView(content).to_dict()

    # -- W --

    def write(self, data: str):
        """
        Write in the file
        """
        mode = "a+"+self._mode
        with self.open(mode) as fp:
            fp.write(data)

    @classmethod
    def get_resource_model_type(cls) -> Type[Any]:
        """Return the resource model associated with this Resource
        //!\\ To overwrite only when you know what you are doing

        :return: [description]
        :rtype: Type[Any]
        """
        from .file_model import FileModel
        return FileModel

    # -- S --

# ####################################################################
#
# FileSet class
#
# ####################################################################


class FileSet(ResourceSet):
    _resource_types = (File,)
