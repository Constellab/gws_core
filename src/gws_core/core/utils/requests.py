# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import re
import sys

import requests


class Requests:
    """
    Requests class
    """

    @staticmethod
    def download(url: str, dest_dir: str, dest_filename: str) -> str:
        """
        Download a file

        :param url: URL of the file
        :type url: `str`
        :param dest_dir: Destimation directory of the dwonladed file
        :type dest_dir: `str`
        :param dest_filename: Name of the downloaded file
        :type dest_filename: `str`
        :return: The path of the downloaed file
        :rtype: `str`
        """

        dest_file_path = os.path.join(dest_dir, dest_filename)
        print(f"Downloading {url} to {dest_file_path} ...")

        if os.path.exists(dest_file_path):
            print(f"Data {dest_file_path} already exists")
            return None

        if dest_file_path.endswith(".zip"):
            if os.path.exists(re.sub(r"\.zip$", "", dest_file_path)):
                print(f"Unzipped data {dest_file_path} already exists")
                return None

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        with open(dest_file_path, 'wb') as f:
            response = requests.get(url, stream=True)
            total = response.headers.get('content-length')

            if total is None:
                f.write(response.content)
            else:
                downloaded = 0
                total = int(total)
                for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                    downloaded += len(data)
                    f.write(data)
                    done = int(50*downloaded/total)
                    sys.stdout.write('\r[{}{}]'.format(
                        '█' * done, '.' * (50-done)))
                    sys.stdout.flush()

        sys.stdout.write('\n')

        return dest_file_path
