
import os
from unittest import IsolatedAsyncioTestCase

from gws_core import Settings
from gws_core.core.utils.zip import Zip
from gws_core.impl.file.file_helper import FileHelper


class TestDate(IsolatedAsyncioTestCase):

    def test_zip_unzip(self):

        # Init folder to zip
        temp_dir: str = Settings.retrieve().make_temp_dir()
        to_zip_folder = os.path.join(temp_dir, 'to_zip')
        FileHelper.create_dir_if_not_exist(to_zip_folder)
        FileHelper.create_empty_file_if_not_exist(os.path.join(to_zip_folder, 'test.json'))

        # Zip and check
        zipped_folder = os.path.join(temp_dir, 'zipped.zip')
        Zip.zipdir(to_zip_folder, zipped_folder)
        FileHelper.exists_on_os(zipped_folder)

        # Unzip and check
        Zip.unzip(zipped_folder, os.path.join(temp_dir, 'desitnation'))
        FileHelper.exists_on_os(os.path.join(temp_dir, 'desitnation'))
        FileHelper.exists_on_os(os.path.join(temp_dir, 'desitnation', 'test.json'))