

import os
from unittest import TestCase

from gws_core import FileDownloader, Settings
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    BasicMessageObserver
from gws_core.impl.file.file_helper import FileHelper
from gws_core.task.task_file_downloader import TaskFileDownloader

settings = Settings.get_instance()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


# test_file_downloader
class TestFileDownloader(TestCase):

    def test_download(self):
        message_dispatcher = MessageDispatcher(0, 0)
        message_obs = BasicMessageObserver()
        message_dispatcher.attach(message_obs)

        destination_folder = Settings.get_instance().make_temp_dir()
        file_downloader = FileDownloader(
            destination_folder, message_dispatcher)

        url = "https://storage.gra.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/opendata/gws_core/iris.csv"
        filename = "my_file.pdf"

        # download the file and check the destination path
        file_path = file_downloader.download_file_if_missing(
            url, filename, timeout=60)
        self.assertEqual(os.path.join(destination_folder, filename), file_path)
        self.assertTrue(os.path.exists(file_path))

        # there should be at least 3 message, 1 for the download start, 1 for the download end
        # and 1 for the progress bar
        message_dispatcher.force_dispatch_waiting_messages()
        self.assertTrue(len(message_obs.messages) > 2)

        # clean up
        FileHelper.delete_dir(destination_folder)
        self.assertFalse(os.path.exists(destination_folder))

    def test_task_file_downloader(self):
        task_file_downloader = TaskFileDownloader('gws_core', None)

        file_destination = os.path.join(
            task_file_downloader.destination_folder, "my_file.pdf")

        if FileHelper.exists_on_os(file_destination):
            FileHelper.delete_file(file_destination)

        url = "https://storage.gra.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/opendata/gws_core/iris.csv"
        task_file_downloader.download_file_if_missing(
            url, "my_file.pdf", timeout=60)

        # check the file has been downloaded
        self.assertTrue(FileHelper.exists_on_os(file_destination))

    def test_file_zip_downloader(self):
        message_dispatcher = MessageDispatcher(0, 0)
        message_obs = BasicMessageObserver()
        message_dispatcher.attach(message_obs)

        destination_folder = Settings.get_instance().make_temp_dir()
        file_downloader = FileDownloader(
            destination_folder, message_dispatcher)

        url = "https://storage.sbg.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/public/gws_core_test_file_downloader.zip"
        folder_name = "gws_core_test_file_downloader"

        # download the file and check the destination path
        folder_path = file_downloader.download_file_if_missing(
            url, folder_name, decompress_file=True, timeout=60)
        self.assertEqual(os.path.join(
            destination_folder, folder_name), folder_path)
        self.assertTrue(os.path.exists(folder_path))

        # there should be at least 3 message, 1 for the download start, 1 for the download end
        # and 1 for the progress bar
        message_dispatcher.force_dispatch_waiting_messages()
        self.assertTrue(len(message_obs.messages) > 2)

        # clean up
        FileHelper.delete_dir(destination_folder)
        self.assertFalse(os.path.exists(destination_folder))
