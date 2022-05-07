# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import mimetypes
import os
import shutil
from pathlib import Path
from re import sub
from typing import Any, List, Union

from charset_normalizer import from_path

PathType = Union[str, Path]


class FileHelper():
    """
    Class containing only classmethod to simplify file management
    """

    LARGE_SIZE_IN_BYTES = 20*1e6   # 20 MB

    @classmethod
    def get_dir(cls, path: PathType) -> Path:
        return cls.get_path(path).parent

    @classmethod
    def get_size(cls, path: PathType) -> int:
        if cls.is_file(path):
            return os.path.getsize(path)

        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                fp = os.path.join(dirpath, filename)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return total_size

    # -- E --

    @classmethod
    def get_extension(cls, path: PathType):
        return cls.get_path(path).suffix

    @classmethod
    def get_name(cls, path: PathType):
        return cls.get_path(path).stem

    @classmethod
    def get_dir_name(cls, path: PathType):
        return os.path.basename(path)

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

    @classmethod
    def create_empty_file_if_not_exist(cls, file_path: PathType) -> Path:
        path: Path = cls.get_path(file_path)
        if cls.exists_on_os(path):
            return path

        path.touch()
        return path

    @classmethod
    def create_dir_if_not_exist(cls, dir_path: PathType) -> Path:
        path: Path = cls.get_path(dir_path)
        if cls.exists_on_os(path):
            return path

        os.makedirs(path)
        return path

    @classmethod
    def is_large(cls, path: PathType):
        return cls.get_size(path) > cls.LARGE_SIZE_IN_BYTES

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

    @classmethod
    def is_file(cls, path: PathType):
        return os.path.isfile(path)

    @classmethod
    def is_dir(cls, path: PathType):
        return os.path.isdir(path)

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

    @classmethod
    def delete_dir(cls, dir_path: PathType, ignore_errors: bool = True) -> None:
        path = cls.get_path(dir_path)
        shutil.rmtree(path=path, ignore_errors=ignore_errors)

    @classmethod
    def delete_file(cls, file_path: PathType) -> None:
        path = cls.get_path(file_path)
        os.remove(path)

    @classmethod
    def delete_node(cls, node_path: PathType) -> None:
        if cls.is_dir(node_path):
            cls.delete_dir(node_path)
        else:
            cls.delete_file(node_path)

    @classmethod
    def get_dir_content_as_json(cls, path: PathType) -> Any:
        if cls.is_file(path):
            return cls.get_name_with_extension(path)

        if cls.is_dir(path):
            children: List[str] = os.listdir(path)
            result: List[Any] = []

            for child in children:
                result.append(cls.get_dir_content_as_json(os.path.join(path, child)))
            dir_name: str = cls.get_dir_name(path)
            return {dir_name: result}

        return None

    @classmethod
    def sanitize_name(cls, name: str) -> str:
        """Sanitize a file name, folder name or path in order to prevent injection when using the file name
            Basically, it keeps only the alphanumeric characters and -,_,\,/
        """
        return sub(r"[^a-zA-Z0-9-_/.]", '', name)

    @classmethod
    def detect_file_encoding(cls, file_path: PathType, default_encoding: str = 'utf-8') -> str:
        """Detect the encoding of a file """

        if not cls.exists_on_os(file_path):
            return default_encoding

        encoding_result = from_path(file_path)
        if encoding_result.best():
            return encoding_result.best().encoding
        else:
            return default_encoding
