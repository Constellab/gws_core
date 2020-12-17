
import asyncio
import unittest
import os

from gws.settings import Settings
from gws.file import File

  
class TestFile(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        File.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        File.drop_table()
        pass
    
    def test_file(self):
        f = File()
        f.path = "/oui/non"
        f.save()
        
        self.assertTrue(f.is_saved())