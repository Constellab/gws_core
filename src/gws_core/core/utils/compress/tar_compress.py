
from tarfile import TarFile
from tarfile import open as tar_open

from .compress import Compress


class TarCompress(Compress):
    """Class to compress and uncompress tar file.

    :return: _description_
    :rtype: _type_
    """

    tar_file: TarFile

    compress_option: str = ''

    def __init__(self, destination_file_path: str):
        super().__init__(destination_file_path)
        self.tar_file = tar_open(destination_file_path, "w" + self.compress_option)

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

        with tar_open(file_path, "r" + cls.compress_option) as tar:
            tar.extractall(destination_folder)

    @classmethod
    def can_uncompress_file(cls, file_path: str) -> bool:
        """Return true if the file can be uncompressed by this class
        """
        return file_path.endswith('.tar')


class TarGzCompress(TarCompress):
    """Class to compress and uncompress tar.gz file.

    :return: _description_
    :rtype: _type_
    """

    tar_file: TarFile

    compress_option: str = ':gz'

    @classmethod
    def can_uncompress_file(cls, file_path: str) -> bool:
        """Return true if the file can be uncompressed by this class
        """
        return file_path.endswith('.tar.gz')
