# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from tarfile import TarFile, open

from .compress import Compress


class TarCompress(Compress):
    """Class to compress and uncompress tar.gz file.

    :return: _description_
    :rtype: _type_
    """

    tar_file: TarFile

    supported_extensions = ['tar.gz']

    def __init__(self, destination_file_path: str):
        super().__init__(destination_file_path)
        self.tar_file = open(destination_file_path, "w:gz")

    def add_dir(self, dir_path: str, dir_name: str = None) -> None:
        dir_name = self._generate_node_name(dir_path, dir_name)

        self.tar_file.add(dir_path, arcname=dir_name)

    def add_file(self, file_path: str, file_name: str = None) -> None:
        file_name = self._generate_node_name(file_path, file_name)
        self.tar_file.add(file_path, arcname=file_name)

    def close(self) -> str:
        self.tar_file.close()
        return self.destination_file_path

    @classmethod
    def decompress(cls, file_path: str, destination_folder: str) -> None:
        """
        Uncompress a tar.gz file.

        :param tar_gz_file_path: Path of the tar.gz file to uncompress
        :param tar_gz_file_path: `str`
        """

        tar = open(file_path, "r:gz")
        tar.extractall(destination_folder)
        tar.close()
