# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import os
import time
from typing import Dict

import requests

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.utils.compress.compress import Compress
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class FileDownloader():
    """Class to downloader external files. for now it only supports http(s) protocol.
    If a message dispatcher is provided, it will automatically log the download progress and the time it took to download the file.
    """

    message_dispatcher: MessageDispatcher
    destination_folder: str

    def __init__(self, destination_folder: str, message_dispatcher: MessageDispatcher = None):
        self.destination_folder = destination_folder
        self.message_dispatcher = message_dispatcher

    def download_file_if_missing(self, url: str, filename: str, headers: Dict[str, str] = None,
                                 timeout: float = None, decompress_file: bool = False) -> str:
        """ Download a file from a given url if the file does not already exist. This class is useful for downloading
        a file that is required for a task.
        If used within a task, it automatically logs the download progress and the time it took to download the file.

        :param url: url to download the file from
        :type url: str
        :param filename: name of the file once downloaded. This filename must be unique for the brick. If a file downloader
                         tries to download a file with the same name, it considers that the file has already been downloaded
                         and will not download it. If you want to force the download of a file (new version for example), change the filename (adding v2 for example).
        :type filename: str
        :param headers: http header to attach to the download request, defaults to None
        :type headers: Dict[str, str], optional
        :param timeout: timeout of the download request, defaults to None
        :type timeout: float, optional
        :param decompress_file: if true the file is decompress (support .zip and .tar.gz) after the download and the zip file is deleted, defaults to False
        :type decompress_file: bool, optional
        :return: the path of the downloaded file/folder
        :rtype: str
        """

        FileHelper.create_dir_if_not_exist(self.destination_folder)

        file_path = os.path.join(self.destination_folder, filename)

        if self._check_if_already_downloaded(file_path):
            self._dispatch_message(f"File {file_path} already downloaded")
            return file_path

        if decompress_file:
            # retrieve filename from url
            url_filename = url.split('/')[-1]
            temp_dir = Settings.make_temp_dir()
            download_destination = os.path.join(temp_dir, url_filename)
        else:
            # If the file needs to be unzipped, we need to download it to a temporary folder
            download_destination = file_path
        self.download_file(url, download_destination, headers, timeout)

        if decompress_file:
            return self.decompress_file(download_destination, file_path)

        return file_path

    def download_file(self, url: str, destination_path: str, headers: Dict[str, str] = None,
                      timeout: float = None) -> str:
        """
        Download a file from a given url to a given file path

        :param url: The url to download the file from
        :type url: `str`
        :param file_path: The complete path to save the file to (including file name)
        :type file_path: `str`
        :param headers: The headers to send with the request
        :type headers: `dict`
        """

        self._dispatch_message(f"Downloading {url} to {destination_path}")
        started_at = time.time()

        try:
            with requests.get(url, stream=True, headers=headers, timeout=timeout) as request:
                request.raise_for_status()

                with open(destination_path, 'wb') as file:

                    if request.headers.get('content-length') is None:
                        file.write(request.content)
                    else:
                        # download the file in chunks with a progress bar
                        total_size = int(request.headers.get('content-length'))
                        last_progress_logged = 0.0

                        # convert a to int and if it fails, use None
                        for chunk in request.iter_content(chunk_size=max(int(total_size/1000), 1024*1024)):
                            file.write(chunk)

                            downloaded_size = file.tell()
                            progress = downloaded_size / total_size

                            # if the progress is less than 3% more than the previous log, do not display the progress
                            if progress - last_progress_logged > 0.03:
                                # calculate remaining time
                                remaining_time = (
                                    time.time() - started_at) / (downloaded_size / total_size) - (time.time() - started_at)

                                self._dispatch_progress(
                                    total_size, downloaded_size, remaining_time)
                                last_progress_logged = progress

        except Exception as exc:
            self._dispatch_error(
                f"Error downloading {url} to {destination_path}: {exc}")
            raise exc

        duration = DateHelper.get_duration_pretty_text(
            time.time() - started_at)
        self._dispatch_message(
            f"Downloaded {url} to {destination_path} in {duration}")

        return destination_path

    def decompress_file(self, file_path: str, destination_folder: str) -> str:
        """
        Unzip a file to a given path

        :param file_path: The path to the file to unzip
        :type file_path: `str`
        :param unzip_path: The path to unzip the file to
        :type unzip_path: `str`
        """

        self._dispatch_message(
            f"Unzipping {file_path} to {destination_folder}")
        started_at = time.time()

        try:
            Compress.smart_decompress(file_path, destination_folder)
        except Exception as exc:
            self._dispatch_error(
                f"Error unzipping {file_path} to {destination_folder}: {exc}")
            raise exc

        duration = DateHelper.get_duration_pretty_text(
            time.time() - started_at)
        self._dispatch_message(
            f"Unzipped {file_path} to {destination_folder} in {duration}")

        # delete zip file
        FileHelper.delete_file(file_path)

        return destination_folder

    def _check_if_already_downloaded(self, file_path: str) -> bool:
        """
        Check if a file exists

        :param file_path: The path to the file to check
        :type file_path: `str`
        :return: True if the file exists, False otherwise
        :rtype: `bool`
        """
        return FileHelper.exists_on_os(file_path)

    def _dispatch_progress(self, total: int, downloaded: int, remaining_time: float) -> None:
        """
        Dispatch the progress of the download

        :param total: The total size of the file to download
        :type total: `int`
        :param downloaded: The amount of data downloaded so far
        :type downloaded: `int`
        """
        if self.message_dispatcher is not None:
            downloaded_str = FileHelper.get_file_size_pretty_text(downloaded)
            total_str = FileHelper.get_file_size_pretty_text(total)
            percent = round(downloaded / total * 100)

            remaining_time_str = DateHelper.get_duration_pretty_text(
                remaining_time)
            self.message_dispatcher.notify_info_message(
                f"Downloaded {downloaded_str}/{total_str} ({percent}%) - {remaining_time_str} remaining"
            )

    def _dispatch_message(self, message: str) -> None:
        """
        Dispatch a message

        :param message: The message to dispatch
        :type message: `dict`
        """
        if self.message_dispatcher is not None:
            self.message_dispatcher.notify_info_message(message)

    def _dispatch_error(self, message: str) -> None:
        """
        Dispatch an error message

        :param message: The error message to dispatch
        :type message: `str`
        """
        if self.message_dispatcher is not None:
            self.message_dispatcher.notify_error_message(message)
