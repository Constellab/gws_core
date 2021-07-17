# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import unittest

from gws.settings import Settings
from gws.requests import Requests
from gws.unittest import GTest

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")

class TestRequests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    
    def test_download(self):
        GTest.print("Download Requests")

        url = "https://www.biorxiv.org/content/10.1101/2020.02.16.951624v1.full.pdf"
        filename = "my_file.pdf"
        if os.path.exists(os.path.join(testdata_dir,filename)):
            os.remove(os.path.join(testdata_dir,filename))

        file_path = Requests.download(url, dest_dir=testdata_dir, dest_filename=filename)
        self.assertTrue(bool(file_path))
        self.assertTrue(os.path.exists(file_path))
        os.remove(file_path)
        self.assertTrue(not os.path.exists(file_path))
