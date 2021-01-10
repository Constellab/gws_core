
import asyncio
import unittest
import os

from gws.settings import Settings
from gws.file import File
from gws.store import FileStore

  
class TestFile(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        FileStore.remove_all_files(ignore_errors=True)
        File.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        pass
    
    def test_file(self):
        f = FileStore.create_file(name="my_file.txt")
        f.save()
        self.assertTrue(f.is_saved())
        
        f.write("Hi.\n")
        f.write("My name is John")
        
        text = f.read()
        self.assertTrue(text, "Hi.\nMy name is John")