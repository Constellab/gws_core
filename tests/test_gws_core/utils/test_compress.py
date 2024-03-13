

import os
from unittest import TestCase

from gws_core import (Compress, GzipCompress, Settings, TarCompress,
                      TarGzCompress, ZipCompress)
from gws_core.impl.file.file_helper import FileHelper


# test_compress
class TestCompress(TestCase):

    def test_zip_unzip(self):

        # Init folder to zip
        temp_dir: str = Settings.get_instance().make_temp_dir()
        to_zip_folder = os.path.join(temp_dir, 'to_zip')
        FileHelper.create_dir_if_not_exist(to_zip_folder)
        FileHelper.create_empty_file_if_not_exist(
            os.path.join(to_zip_folder, 'test.json'))

        # Zip and check
        zipped_folder = os.path.join(temp_dir, 'zipped.zip')
        ZipCompress.compress_dir(to_zip_folder, zipped_folder)
        self.assertTrue(FileHelper.exists_on_os(zipped_folder))

        # Unzip and check
        destination_folder = os.path.join(temp_dir, 'destination')
        ZipCompress.decompress(zipped_folder, destination_folder)
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
        TarGzCompress.compress_dir(to_zip_folder, compress_folder)
        self.assertTrue(FileHelper.exists_on_os(compress_folder))

        # Decompress and check
        destination_folder = os.path.join(temp_dir, 'destination')
        TarGzCompress.decompress(compress_folder, destination_folder)
        self.assertTrue(FileHelper.exists_on_os(destination_folder))
        self.assertTrue(FileHelper.exists_on_os(os.path.join(
            destination_folder, 'to_zip',  'test.json')))

    def test_tar(self):
        # Init folder to zip
        temp_dir: str = Settings.get_instance().make_temp_dir()
        to_zip_folder = os.path.join(temp_dir, 'to_zip')
        FileHelper.create_dir_if_not_exist(to_zip_folder)
        FileHelper.create_empty_file_if_not_exist(
            os.path.join(to_zip_folder, 'test.json'))

        # Compress and check
        compress_folder = os.path.join(temp_dir, 'zipped.tar')
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
