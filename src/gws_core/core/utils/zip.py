# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from zipfile import ZIP_DEFLATED, ZipFile

from gws_core.impl.file.file_helper import FileHelper


class Zip:
    """
    Zip class
    """

    destination_file_path: str
    zipf: ZipFile

    def __init__(self, destination_file_path: str):
        self.destination_file_path = destination_file_path
        self.zipf = ZipFile(destination_file_path, 'w', ZIP_DEFLATED)

    def add_dir(self, dir_to_zip: str, dir_name: str = None) -> None:
        if dir_name is None:
            dir_name = FileHelper.get_name(dir_to_zip)

        # ziph is zipfile handle
        for root, _, files in os.walk(dir_to_zip):
            for file in files:
                new_path = root.replace(dir_to_zip, dir_name)
                self.zipf.write(os.path.join(root, file),
                                os.path.join(new_path, file))

    def add_file(self, file_path: str, file_name: str = None) -> None:
        if file_name is None:
            file_name = FileHelper.get_name(file_path)
        self.zipf.write(file_path, file_name)

    def add_fs_node(self, fs_node_path: str, fs_node_name: str = None) -> None:
        if FileHelper.is_dir(fs_node_path):
            self.add_dir(fs_node_path, fs_node_name)
        else:
            self.add_file(fs_node_path, fs_node_name)

    def close(self) -> str:
        self.zipf.close()
        return self.destination_file_path

    @staticmethod
    def unzip(zipfile_path: str, destination_folder: str):
        """
        Unzip a file.

        :param zipfile_path: Path of the file to unzip
        :param zipfile_path: `str`
        """

        with ZipFile(zipfile_path, 'r') as zip_obj:
            zip_obj.extractall(destination_folder)

    @staticmethod
    def zipdir(dir_to_zip: str, destination_file_path: str) -> str:
        """Static method to zip 1 directory directly.

        :param dir_to_zip: _description_
        :type dir_to_zip: str
        :param destination_file_path: _description_
        :type destination_file_path: str
        :return: _description_
        :rtype: str
        """

        zip_ = Zip(destination_file_path)
        zip_.add_dir(dir_to_zip)
        return zip_.close()
