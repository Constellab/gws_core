# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import gzip
import os
import shutil

from gws_core.impl.file.file_helper import FileHelper

from .compress import Compress


class GzipCompress(Compress):
    """Class to compress and uncompress gz file.

    :return: _description_
    :rtype: _type_
    """

    file_path: str = None

    def add_dir(self, dir_path: str, dir_name: str = None) -> None:
        raise Exception('GzipCompress does not support directory')

    def add_file(self, file_path: str, file_name: str = None) -> None:
        if self.file_path is not None:
            raise Exception('GzipCompress does not support multiple file')
        self.file_path = file_path

    def close(self) -> str:
        if self.file_path is None:
            raise Exception('No file added to the GzipCompress')

        with open(self.file_path, 'rb') as input_file:
            with gzip.open(self.destination_file_path, 'wb') as gzipped_file:
                gzipped_file.writelines(input_file)

        return self.destination_file_path

    @classmethod
    def decompress(cls, file_path: str, destination_folder: str) -> None:
        """
        Uncompress a gz into a txt file.

        :param tar_gz_file_path: Path of the tar.gz file to uncompress
        :param tar_gz_file_path: `str`
        """
        file_name = FileHelper.get_name(file_path) + '.txt'
        decompress_file_path = os.path.join(destination_folder, file_name)

        # create destination folder if not exist
        FileHelper.create_dir_if_not_exist(destination_folder)

        with gzip.open(file_path, 'rb') as f_in:
            with open(decompress_file_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    @classmethod
    def can_uncompress_file(cls, file_path: str) -> bool:
        """Return true if the file can be uncompressed by this class
        """
        if file_path.endswith('.tar.gz'):
            return False
        return file_path.endswith('.gz')
