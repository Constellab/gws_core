
import mimetypes
import os
from pathlib import Path
from typing import List, Union

PathType = Union[str, Path]


class FileHelper():
    """
    Class containing only classmethod to simplify file management
    """

    csv_dilimiters: List[str] = ['\t', ',', ';']

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

        for delimiter in cls.csv_dilimiters:
            count: int = sub_csv.count(delimiter)
            if(count > max_delimiter_count):
                max_delimiter = delimiter
                max_delimiter_count = count

        return max_delimiter
