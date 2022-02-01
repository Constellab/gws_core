# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from zipfile import ZIP_DEFLATED, ZipFile


class Zip:
    """
    Zip class
    """

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
        zipf = ZipFile(destination_file_path, 'w', ZIP_DEFLATED)

        # ziph is zipfile handle
        for root, dirs, files in os.walk(dir_to_zip):
            for file in files:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file),
                                           os.path.join(dir_to_zip, '..')))

        zipf.close()
        return destination_file_path
