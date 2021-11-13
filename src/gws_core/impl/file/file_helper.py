
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Any, List, Union

PathType = Union[str, Path]


class FileHelper():
    """
    Class containing only classmethod to simplify file management
    """

    LARGE_SIZE_IN_BYTES = 20*1e6   # 20 MB
    CSV_DELIMITERS: List[str] = ['\t', ',', ';']

    @classmethod
    def get_dir(cls, path: PathType) -> Path:
        return cls.get_path(path).parent

    @classmethod
    def get_size(cls, path: PathType) -> int:
        return os.path.getsize(path)

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
    def detect_csv_delimiter(cls, csv_str: str) -> str:
        """Method to guess the delimiter of a csv string based on delimiter count
        """
        if csv_str is None or len(csv_str) < 10:
            return None

        max_delimiter: str = None
        max_delimiter_count: int = 0

        # use a sub csv to improve speed
        sub_csv = csv_str[0:10000]

        for delimiter in cls.CSV_DELIMITERS:
            count: int = sub_csv.count(delimiter)
            if(count > max_delimiter_count):
                max_delimiter = delimiter
                max_delimiter_count = count

        return max_delimiter

    @classmethod
    def delete_dir(cls, dir_path: PathType, ignore_errors: bool = True) -> None:
        path = cls.get_path(dir_path)
        shutil.rmtree(path=path, ignore_errors=ignore_errors)

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
