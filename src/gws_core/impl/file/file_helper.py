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
from fastapi.responses import FileResponse

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
        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                fp = os.path.join(dirpath, filename)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return total_size

    # -- E --

    @classmethod
    def get_extension(cls, path: PathType) -> str:
        """Return the extension of a file without the '.'.
        Return None if no extension is found (like folder).
        """
        extension = cls.clean_extension(cls.get_path(path).suffix)

        if extension == '':
            return None
        return extension

    @classmethod
    def clean_extension(cls, extension: str) -> str:
        """Return the extension of a file without the '.' if it is present on first caracter"""
        if extension is None:
            return None

        return sub(r'^\.', '', extension)

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
    def is_large(cls, path: PathType) -> bool:
        return cls.get_size(path) > cls.LARGE_SIZE_IN_BYTES

    @classmethod
    def is_json(cls, path: PathType) -> bool:
        return cls.get_extension(path) in ["json"]

    @classmethod
    def is_csv(cls, path: PathType) -> bool:
        return cls.get_extension(path) in ["csv", "tsv"]

    @classmethod
    def is_txt(cls, path: PathType) -> bool:
        return cls.get_extension(path) in ["txt"]

    @classmethod
    def is_jpg(cls, path: PathType) -> bool:
        return cls.get_extension(path) in ["jpg", "jpeg"]

    @classmethod
    def is_png(cls, path: PathType) -> bool:
        return cls.get_extension(path) in ["png"]

    @classmethod
    def is_image(cls, path: PathType) -> bool:
        return cls.get_extension(path) in ["jpg", "jpeg", "png", "gif", "bmp", "tiff",
                                           "tif", "svg", "svgz", "heic", "heif", "heics",
                                           "heifs", "jp2", "j2k", "jpf", "jpx", "jpm", "mj2",
                                           "jfif", "webp", "avif", "apng", "ico"]

    @classmethod
    def is_file(cls, path: PathType) -> bool:
        return os.path.isfile(path)

    @classmethod
    def is_dir(cls, path: PathType) -> bool:
        return os.path.isdir(path)

    # -- M --

    @classmethod
    def get_mime(cls, path: PathType) -> str:
        ext: str = cls.get_extension(path)
        if ext:
            # specific case not handled by mimetypes
            if ext == 'jfif':
                return 'image/jpeg'

            return mimetypes.types_map.get('.' + ext)
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
    def delete_file(cls, file_path: PathType, ignore_errors: bool = True) -> None:
        path = cls.get_path(file_path)

        if ignore_errors and not cls.exists_on_os(path):
            return
        os.remove(path)

    @classmethod
    def delete_node(cls, node_path: PathType) -> None:
        if cls.is_dir(node_path):
            cls.delete_dir(node_path)
        else:
            cls.delete_file(node_path)

    @classmethod
    def delete_dir_content(cls, dir_path: PathType) -> None:
        path = cls.get_path(dir_path)
        for child in path.iterdir():
            cls.delete_node(child)

    @classmethod
    def get_dir_content_as_json(cls, path: PathType) -> Any:
        if cls.is_file(path):
            return cls.get_name_with_extension(path)

        if cls.is_dir(path):
            children: List[str] = os.listdir(path)
            result: List[Any] = []

            for child in children:
                result.append(cls.get_dir_content_as_json(
                    os.path.join(path, child)))
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
        best_encoding = encoding_result.best()
        if best_encoding:
            return best_encoding.encoding
        else:
            return default_encoding

    @classmethod
    def copy_file(cls, source_path: PathType, destination_path: PathType) -> None:
        """Copy a file from source to destination"""
        shutil.copyfile(source_path, destination_path)

    @classmethod
    def move_file_or_dir(cls, source_path: PathType, destination_path: PathType) -> None:
        """Move a file or a directory from source to destination"""
        shutil.move(str(source_path), str(destination_path))

    @classmethod
    def create_file_response(cls, file_path: PathType, filename: str = None,
                             media_type: str = None) -> FileResponse:
        """Create a flask response from a file path"""
        if not cls.exists_on_os(file_path):
            raise FileNotFoundError(f'File {file_path} not found')

        if not filename:
            filename = cls.get_name_with_extension(file_path)

        if not media_type:
            media_type = cls.get_mime(file_path)

        return FileResponse(file_path, media_type=media_type, filename=filename)

    @classmethod
    def get_file_size_pretty_text(cls, size: float) -> str:
        """Get a human readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if size < 1024.0:
                return f'{size:.1f} {unit}'
            size /= 1024.0
        return f'{size:.1f} EB'

    @staticmethod
    def generate_unique_fs_node_for_list(list_fs_node_names: List[str], fs_node_name: str) -> str:
        """Generate a unique fs node name for a list of node names.
        Append _1, _2... before the extension if the str is already in the list
        """
        if fs_node_name not in list_fs_node_names:
            return fs_node_name

        i = 1
        name = f"{FileHelper.get_name(fs_node_name)}_{i}.{FileHelper.get_extension(fs_node_name)}" if '.' in fs_node_name else f"{FileHelper.get_name(fs_node_name)}_{i}"
        while name in list_fs_node_names:
            i += 1
            name = f"{FileHelper.get_name(fs_node_name)}_{i}.{FileHelper.get_extension(fs_node_name)}" if '.' in fs_node_name else f"{FileHelper.get_name(fs_node_name)}_{i}"

        return name
