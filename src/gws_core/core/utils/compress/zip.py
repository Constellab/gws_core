# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from zipfile import ZIP_DEFLATED, ZipFile

from .compress import Compress


class Zip(Compress):
    """
    Class to zip and unzip files and folders
    """

    zipf: ZipFile

    supported_extensions = ['zip']

    def __init__(self, destination_file_path: str):
        super().__init__(destination_file_path)
        self.zipf = ZipFile(destination_file_path, 'w', ZIP_DEFLATED)

    def add_dir(self, dir_path: str, dir_name: str = None) -> None:
        dir_name = self._generate_node_name(dir_path, dir_name)

        # ziph is zipfile handle
        for root, _, files in os.walk(dir_path):
            for file in files:
                new_path = root.replace(dir_path, dir_name)
                self.zipf.write(os.path.join(root, file),
                                os.path.join(new_path, file))

    def add_file(self, file_path: str, file_name: str = None) -> None:
        file_name = self._generate_node_name(file_path, file_name)
        self.zipf.write(file_path, file_name)

    def close(self) -> str:
        self.zipf.close()
        return self.destination_file_path

    @classmethod
    def decompress(cls, file_path: str, destination_folder: str) -> None:
        """
        Unzip a file.

        :param zipfile_path: Path of the file to unzip
        :param zipfile_path: `str`
        """

        with ZipFile(file_path, 'r') as zip_obj:
            zip_obj.extractall(destination_folder)