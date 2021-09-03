
import mimetypes
import os
from pathlib import Path
from typing import Union

PathType = Union[str, Path]


class FileHelper():
    """
    Class containing only classmethod to simplify file management
    """

    @classmethod
    def get_dir(cls, path: PathType) -> Path:
        return cls.get_path(path).parent

    # -- E --

    @classmethod
    def get_extension(cls, path: PathType):
        return cls.get_path(path).suffix

    @classmethod
    def get_name(cls, path: PathType):
        return cls.get_path(path).stem

    @classmethod
    def get_name_with_extension(cls, path: PathType):
        return cls.get_path(path).name

    @classmethod
    def exists_on_os(cls, path: PathType):
        """Exist on local machine

        :return: [description]
        :rtype: [type]
        """
        return os.path.exists(cls.get_path(path))

    # -- F --

    # -- I --

    @classmethod
    def is_json(cls, path: PathType):
        return cls.get_extension(path) in [".json"]

    @classmethod
    def is_csv(cls, path: PathType):
        return cls.get_extension(path) in [".csv", ".tsv"]

    @classmethod
    def is_txt(cls, path: PathType):
        return cls.get_extension(path) in [".txt"]

    @classmethod
    def is_jpg(cls, path: PathType):
        return cls.get_extension(path) in [".jpg", ".jpeg"]

    @classmethod
    def is_png(cls, path: PathType):
        return cls.get_extension(path) in [".png"]

    # -- M --

    @classmethod
    def get_mime(cls, path: PathType):
        ext: str = cls.get_extension(path)
        if ext:
            return mimetypes.types_map[ext]
        else:
            return None

    @classmethod
    def get_path(cls, path: PathType) -> Path:
        if isinstance(path, Path):
            return path
        return Path(path)
