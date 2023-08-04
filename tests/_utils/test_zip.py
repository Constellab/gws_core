# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from unittest import TestCase

from gws_core import Settings
from gws_core.core.utils.compress.compress import Compress
from gws_core.core.utils.compress.gzip_compress import GzipCompress
from gws_core.core.utils.compress.tar_compress import TarCompress
from gws_core.core.utils.compress.zip import Zip
from gws_core.impl.file.file_helper import FileHelper


# test_zip
class TestZip(TestCase):

    def test_zip_unzip(self):

        # Init folder to zip
        temp_dir: str = Settings.get_instance().make_temp_dir()
        to_zip_folder = os.path.join(temp_dir, 'to_zip')
        FileHelper.create_dir_if_not_exist(to_zip_folder)
        FileHelper.create_empty_file_if_not_exist(
            os.path.join(to_zip_folder, 'test.json'))

        # Zip and check
        zipped_folder = os.path.join(temp_dir, 'zipped.zip')
        Zip.compress_dir(to_zip_folder, zipped_folder)
        self.assertTrue(FileHelper.exists_on_os(zipped_folder))

        # Unzip and check
        destination_folder = os.path.join(temp_dir, 'destination')
        Zip.decompress(zipped_folder, destination_folder)
        self.assertTrue(FileHelper.exists_on_os(destination_folder))
        self.assertTrue(FileHelper.exists_on_os(
            os.path.join(destination_folder, 'to_zip', 'test.json')))

        # test smart compress
        FileHelper.delete_dir(destination_folder)
        self.assertFalse(FileHelper.exists_on_os(destination_folder))
        Compress.smart_decompress(zipped_folder, destination_folder)
        self.assertTrue(FileHelper.exists_on_os(destination_folder))
        self.assertTrue(FileHelper.exists_on_os(
            os.path.join(destination_folder, 'to_zip', 'test.json')))

    def test_tar_gz(self):
        # Init folder to zip
        temp_dir: str = Settings.get_instance().make_temp_dir()
        to_zip_folder = os.path.join(temp_dir, 'to_zip')
        FileHelper.create_dir_if_not_exist(to_zip_folder)
        FileHelper.create_empty_file_if_not_exist(
            os.path.join(to_zip_folder, 'test.json'))

        # Compress and check
        compress_folder = os.path.join(temp_dir, 'zipped.tar.gz')
        TarCompress.compress_dir(to_zip_folder, compress_folder)
        self.assertTrue(FileHelper.exists_on_os(compress_folder))

        # Decompress and check
        destination_folder = os.path.join(temp_dir, 'destination')
        TarCompress.decompress(compress_folder, destination_folder)
        self.assertTrue(FileHelper.exists_on_os(destination_folder))
        self.assertTrue(FileHelper.exists_on_os(os.path.join(
            destination_folder, 'to_zip',  'test.json')))

    def test_gz(self):
        # Init folder to zip
        temp_dir: str = Settings.get_instance().make_temp_dir()
        to_zip_folder = os.path.join(temp_dir, 'to_zip')
        FileHelper.create_dir_if_not_exist(to_zip_folder)
        json_path = FileHelper.create_empty_file_if_not_exist(
            os.path.join(to_zip_folder, 'test.json'))

        # Compress and check
        compress_folder = os.path.join(temp_dir, 'zipped.gz')
        compress = GzipCompress(compress_folder)
        compress.add_file(json_path)
        compress.close()
        self.assertTrue(FileHelper.exists_on_os(compress_folder))

        # Decompress and check
        destination_folder = os.path.join(temp_dir, 'destination')
        GzipCompress.decompress(compress_folder, destination_folder)
        self.assertTrue(FileHelper.exists_on_os(destination_folder))
        self.assertTrue(FileHelper.exists_on_os(os.path.join(
            destination_folder, 'zipped.txt')))
