# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from abc import abstractmethod
from typing import List

from gws_core.impl.file.file_helper import FileHelper


class Compress:
    """Abstract class for compress class
    """

    destination_file_path: str

    # list of the fs node name added to the zip
    _fs_node_names: List[str]

    supported_extensions = []

    def __init__(self, destination_file_path: str):
        self.destination_file_path = destination_file_path
        self._fs_node_names = []

    @abstractmethod
    def add_dir(self, dir_path: str, dir_name: str = None) -> None:
        pass

    @abstractmethod
    def add_file(self, file_path: str, file_name: str = None) -> None:
        pass

    @abstractmethod
    def close(self) -> str:
        pass

    def add_fs_node(self, fs_node_path: str, fs_node_name: str = None) -> None:
        if FileHelper.is_dir(fs_node_path):
            self.add_dir(fs_node_path, fs_node_name)
        else:
            self.add_file(fs_node_path, fs_node_name)

    def _generate_node_name(self, fs_node_path: str, fs_node_name: str = None) -> str:
        """Generate a unique name for the fs node. Use the node name if fs_node_name is None.
        """
        if fs_node_name is None:
            fs_node_name = FileHelper.get_name(fs_node_path)

        # avoid duplicate name
        fs_node_name = FileHelper.generate_unique_fs_node_for_list(
            self._fs_node_names, fs_node_name)
        # store the name to avoid duplicate
        self._fs_node_names.append(fs_node_name)
        return fs_node_name

    @classmethod
    @abstractmethod
    def decompress(cls, file_path: str, destination_folder: str):
        """
        Uncompress a tar.gz file.

        :param tar_gz_file_path: Path of the tar.gz file to uncompress
        :param tar_gz_file_path: `str`
        """

    @classmethod
    def compress_dir(cls, dir_path: str, destination_file_path: str) -> None:
        """
        Compress a folder into a tar.gz file.

        :param folder_to_compress: Path of the folder to compress
        :param folder_to_compress: `str`
        :param destination_file_path: Path of the tar.gz file to create
        :param destination_file_path: `str`
        """

        compress = cls(destination_file_path)
        compress.add_dir(dir_path)
        compress.close()

    @staticmethod
    def smart_decompress(file_path: str, destination_folder: str):
        """Detect the extension of the compressed file and use the right decompress method.
        """
        from .tar_compress import TarCompress
        from .zip import Zip
        file_extension = FileHelper.get_extension(file_path)

        if file_extension in Zip.supported_extensions:
            Zip.decompress(file_path, destination_folder)
        elif file_extension in TarCompress.supported_extensions:
            TarCompress.decompress(file_path, destination_folder)
        else:
            raise Exception(f"Unsupported file extension: {file_extension}")
