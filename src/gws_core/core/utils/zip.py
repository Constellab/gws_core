# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from zipfile import ZipFile

class Zip:
    """
    Zip class
    """

    @staticmethod
    def unzip(zipfile_path):
        """
        Unzip a file.

        :param zipfile_path: Path of the file to unzip
        :param zipfile_path: `str`
        """

        print(f"Extracting {zipfile_path} ...")
        with ZipFile(zipfile_path, 'r') as zip_obj:
            path = os.path.dirname(zipfile_path)
            zip_obj.extractall(path)
        print("Extraction finished.")