

import mimetypes
import os
import shutil
from pathlib import Path
from re import sub
from typing import Any, List, Literal, Union

from charset_normalizer import from_path
from fastapi.responses import FileResponse

PathType = Union[str, Path]


class FileHelper():
    """
    Class containing only classmethod to simplify file management
    """

    @classmethod
    def get_dir(cls, path: PathType) -> Path:
        """
        Return the parent directory of a file or a folder

        :param path: path to the file or folder
        :type path: PathType
        :return: parent directory
        :rtype: Path
        """
        return cls.get_path(path).parent

    @classmethod
    def get_size(cls, path: PathType) -> int:
        """
        Return the size of a file or a folder.
        For folder, it is the sum of the size of all files in the folder (recursive).

        :param path: path to the file or folder
        :type path: PathType
        :return: size in bytes
        :rtype: int
        """

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

    @classmethod
    def get_extension(cls, path: PathType) -> str:
        """
        Return the extension of a file without the '.'.
        Return None if no extension is found (like folder).

        :param path: path to the file or folder
        :type path: PathType
        :return: extension of the file
        :rtype: str
        """
        extension = cls.clean_extension(cls.get_path(path).suffix)

        if extension == '':
            return None
        return extension

    @classmethod
    def clean_extension(cls, extension: str) -> str:
        """
        Return the extension of a file without the '.' if it is present on first caracter

        :param extension: extension of the file
        :type extension: str
        :return: cleaned extension
        :rtype: str
        """
        if extension is None:
            return None

        return sub(r'^\.', '', extension)

    @classmethod
    def get_name(cls, path: PathType):
        """
        Return the name of the file without the extension or the name of the folder

        :param path: path to the file or folder
        :type path: PathType
        :return: name of the file or folder
        :rtype: _type_
        """
        return cls.get_path(path).stem

    @classmethod
    def get_dir_name(cls, path: PathType):
        """
        Return the name of the folder.
        If the path is a file, return the name of the parent folder.
        If the path is a folder, return the name of the folder.

        :param path: path to the file or folder
        :type path: PathType
        :return: name of the folder
        :rtype: _type_
        """
        return os.path.basename(path)

    @classmethod
    def get_name_with_extension(cls, path: PathType):
        """
        Return the name of the file with the extension or the name of the folder

        :param path: path to the file or folder
        :type path: PathType
        :return: name of the file or folder
        :rtype: _type_
        """
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
        """
        Create an empty file if it does not exist. Creates intermediate directories if needed.

        :param file_path: path to the file
        :type file_path: PathType
        :return: the path of the file
        :rtype: Path
        """
        path: Path = cls.get_path(file_path)
        if cls.exists_on_os(path):
            return path

        # check if the parent directory exists
        cls.create_dir_if_not_exist(cls.get_dir(path))

        path.touch()
        return path

    @classmethod
    def create_dir_if_not_exist(cls, dir_path: PathType) -> Path:
        """
        Create a directory and all intermediate directories if they do not exist

        :param dir_path: path to the directory
        :type dir_path: PathType
        :return: new directory path
        :rtype: Path
        """
        path: Path = cls.get_path(dir_path)
        if cls.exists_on_os(path):
            return path

        os.makedirs(path)
        return path

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
    def is_audio(cls, path: PathType) -> bool:
        return cls.get_extension(path) in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'aiff', 'alac']

    @classmethod
    def is_video(cls, path: PathType) -> bool:
        return cls.get_extension(path) in ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm']

    @classmethod
    def is_file(cls, path: PathType) -> bool:
        return os.path.isfile(path)

    @classmethod
    def is_dir(cls, path: PathType) -> bool:
        return os.path.isdir(path)

    @classmethod
    def get_mime(cls, path: PathType) -> str:
        ext: str = cls.get_extension(path)
        if ext:
            # specific case not handled by mimetypes
            if ext == 'jfif':
                return 'image/jpeg'

            return mimetypes.types_map.get('.' + ext, 'application/octet-stream')
        else:
            return None

    @classmethod
    def get_extension_from_content_type(cls, content_type: str) -> str:
        """
        Return the extension of a file from its content type

        :param content_type: content type of the file
        :type content_type: str
        :return: extension of the file
        :rtype: str
        """
        return mimetypes.guess_extension(content_type)

    @classmethod
    def get_path(cls, path: PathType) -> Path:
        """
        Return a Path object from a string or a Path object

        :param path: path to convert
        :type path: PathType
        :return: Path object
        :rtype: Path
        """
        if isinstance(path, Path):
            return path
        return Path(path)

    @classmethod
    def delete_dir(cls, dir_path: PathType, ignore_errors: bool = True) -> None:
        """
        Delete a directory and all its content

        :param dir_path: path to the directory
        :type dir_path: PathType
        :param ignore_errors: if True, do not raise an exception if the directory does not exist, defaults to True
        :type ignore_errors: bool, optional
        """
        path = cls.get_path(dir_path)
        shutil.rmtree(path=path, ignore_errors=ignore_errors)

    @classmethod
    def delete_file(cls, file_path: PathType, ignore_errors: bool = True) -> None:
        """
        Delete a file

        :param file_path: path to the file
        :type file_path: PathType
        :param ignore_errors: if True, do not raise an exception if the file does not exist, defaults to True
        :type ignore_errors: bool, optional
        """
        path = cls.get_path(file_path)

        if ignore_errors and not cls.exists_on_os(path):
            return
        os.remove(path)

    @classmethod
    def delete_node(cls, node_path: PathType, ignore_errors: bool = True) -> None:
        """
        Delete a file or a directory

        :param node_path: path to the file or directory
        :type node_path: PathType
        :param ignore_errors: if True, do not raise an exception if the node does not exist, defaults to True
        :type ignore_errors: bool, optional
        """

        if cls.is_dir(node_path):
            cls.delete_dir(node_path, ignore_errors=ignore_errors)
        else:
            cls.delete_file(node_path, ignore_errors=ignore_errors)

    @classmethod
    def delete_dir_content(cls, dir_path: PathType, ignore_errors: bool = True) -> None:
        """
        Delete all the content of a directory but not the directory itself.

        :param dir_path: path to the directory to empty
        :type dir_path: PathType
        :param ignore_errors: if True, do not raise an exception if the directory does not exist, defaults to True
        :type ignore_errors: bool, optional
        """
        path = cls.get_path(dir_path)
        if ignore_errors and not cls.exists_on_os(path):
            return
        for child in path.iterdir():
            cls.delete_node(child)

    @classmethod
    def get_dir_content_as_json(cls, path: PathType) -> Any:
        """
        Return the content of a directory as a json nested object.

        :param path: path to the directory
        :type path: PathType
        :return: content of the directory as a json nested object
        :rtype: Any
        """
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
        """
        Sanitize a file name, folder name or path in order to prevent injection when using the file name
        Basically, it keeps only the alphanumeric characters and -,_,\,/

        :param name: name to sanitize
        :type name: str
        :return: sanitized name
        :rtype: str
        """
        return sub(r"[^a-zA-Z0-9-_/.]", '', name)

    @classmethod
    def detect_file_encoding(cls, file_path: PathType, default_encoding: str = 'utf-8') -> str:
        """
        Detect the encoding of a file using charset-normalizer.

        :param file_path: path to the file
        :type file_path: PathType
        :param default_encoding: default encoding to use if the encoding is not detected, defaults to 'utf-8'
        :type default_encoding: str, optional
        :return: detected encoding
        :rtype: str
        """

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
        """
        Copy a file from source to destination

        :param source_path: source file path
        :type source_path: PathType
        :param destination_path: destination file path
        :type destination_path: PathType
        """
        shutil.copyfile(source_path, destination_path)

    @classmethod
    def copy_dir(cls, source_path: PathType, destination_path: PathType) -> None:
        """
        Copy a directory from source to destination

        :param source_path: source directory path
        :type source_path: PathType
        :param destination_path: destination directory path
        :type destination_path: PathType
        """
        shutil.copytree(source_path, destination_path)

    @classmethod
    def copy_node(cls, source_path: PathType, destination_path: PathType) -> None:
        """
        Copy a file or a directory from source to destination

        :param source_path: source file or directory path
        :type source_path: PathType
        :param destination_path: destination file or directory path
        :type destination_path: PathType
        """
        if cls.is_dir(source_path):
            cls.copy_dir(source_path, destination_path)
        else:
            cls.copy_file(source_path, destination_path)

    @classmethod
    def copy_dir_content_to_dir(cls, source_dir_path: PathType, destination_dir_path: PathType) -> None:
        """
        Copy the content of a directory to another directory

        :param source_dir_path: source directory path
        :type source_dir_path: PathType
        :param destination_dir_path: destination directory path
        :type destination_dir_path: PathType
        """
        for child in os.listdir(cls.get_path(source_dir_path)):
            cls.copy_node(os.path.join(source_dir_path, child),
                          os.path.join(destination_dir_path, child))

    @classmethod
    def move_file_or_dir(cls, source_path: PathType, destination_path: PathType) -> None:
        """
        Move a file or a directory from source to destination

        :param source_path: source file or directory path
        :type source_path: PathType
        :param destination_path: destination file or directory path
        :type destination_path: PathType
        """
        shutil.move(str(source_path), str(destination_path))

    @classmethod
    def create_file_response(cls, file_path: PathType, filename: str = None, media_type: str = None,
                             content_disposition_type: Literal['inline', 'attachment'] = 'attachment') -> FileResponse:
        """
        Create a FastAPI FileResponse from a file path

        :param file_path: path to the file
        :type file_path: PathType
        :param filename: name of the file, defaults to None
        :type filename: str, optional
        :param media_type: media type of the file, defaults to None
        :type media_type: str, optional
        :raises FileNotFoundError: if the file does not exist
        :return: _description_
        :rtype: FileResponse
        """
        if not cls.exists_on_os(file_path):
            raise FileNotFoundError(f'File {file_path} not found')

        if not filename:
            filename = cls.get_name_with_extension(file_path)

        if not media_type:
            media_type = cls.get_mime(file_path)

        return FileResponse(file_path, media_type=media_type, filename=filename,
                            content_disposition_type=content_disposition_type)

    @classmethod
    def get_file_size_pretty_text(cls, size: float) -> str:
        """
        Return a human readable size from a size in bytes.
        Ex : 1024 -> 1 KB

        :param size: size in bytes
        :type size: float
        :return: human readable size
        :rtype: str
        """
        prefix = '-' if size < 0 else ''
        size = abs(size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if size < 1024.0:
                return f'{prefix}{size:.1f} {unit}'
            size /= 1024.0
        return f'{prefix}{size:.1f} EB'

    @staticmethod
    def generate_unique_fs_node_for_dir(fs_node_name: str, dir_path: str) -> str:
        """
        Generate a unique fs node name for a list of node names.
        Append _1, _2... before the extension if the str is already in the list.
        Useful to avoid name collision when adding a file to a directory.

        :param fs_node_name: name of the new fs node
        :type fs_node_name: str
        :param dir_path: path to the directory
        :type dir_path: str
        :return: unique fs node name (= fs_node_name if not in the list, else fs_node_name_1, fs_node_name_2...)
        :rtype: str
        """
        list_fs_node_names = os.listdir(dir_path)
        return FileHelper.generate_unique_fs_node_for_list(list_fs_node_names, fs_node_name)

    @staticmethod
    def generate_unique_fs_node_for_list(list_fs_node_names: List[str], fs_node_name: str) -> str:
        """
        Generate a unique fs node name for a list of node names.
        Append _1, _2... before the extension if the str is already in the list.
        Useful to avoid name collision when adding a file to a directory.

        :param list_fs_node_names: list of existing fs node names
        :type list_fs_node_names: List[str]
        :param fs_node_name: name of the new fs node
        :type fs_node_name: str
        :return: unique fs node name (= fs_node_name if not in the list, else fs_node_name_1, fs_node_name_2...)
        :rtype: str
        """
        if fs_node_name not in list_fs_node_names:
            return fs_node_name

        i = 1
        name = f"{FileHelper.get_name(fs_node_name)}_{i}.{FileHelper.get_extension(fs_node_name)}" if '.' in fs_node_name else f"{FileHelper.get_name(fs_node_name)}_{i}"
        while name in list_fs_node_names:
            i += 1
            name = f"{FileHelper.get_name(fs_node_name)}_{i}.{FileHelper.get_extension(fs_node_name)}" if '.' in fs_node_name else f"{FileHelper.get_name(fs_node_name)}_{i}"

        return name
