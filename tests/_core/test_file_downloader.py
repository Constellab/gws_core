# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import unittest

from gws_core import Settings
from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    BasicMessageObserver
from gws_core.impl.file.file_helper import FileHelper

settings = Settings.get_instance()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


# test_file_downloader
class TestFileDownloader(unittest.TestCase):

    def test_download_2(self):
        message_dispatcher = MessageDispatcher(0, 0)
        message_obs = BasicMessageObserver()
        message_dispatcher.attach(message_obs)

        destination_folder = Settings.get_instance().make_temp_dir()
        file_downloader = FileDownloader(destination_folder, message_dispatcher)

        url = "https://www.biorxiv.org/content/10.1101/2020.02.16.951624v1.full.pdf"
        # url = "https://storage.gra.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/opendata/ubiome/qiime2/sepp-refs-gg-13-8.qza"
        filename = "my_file.pdf"

        # download the file and check the destination path
        file_path = file_downloader.download_file_if_mising(url, filename, timeout=60)
        self.assertEqual(os.path.join(destination_folder, filename), file_path)
        self.assertTrue(os.path.exists(file_path))

        # there should be at least 3 message, 1 for the download start, 1 for the download end
        # and 1 for the progress bar
        message_dispatcher.force_dispatch_waiting_messages()
        self.assertTrue(len(message_obs.messages) > 2)

        # clean up
        FileHelper.delete_dir(destination_folder)
        self.assertFalse(os.path.exists(destination_folder))
