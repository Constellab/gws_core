
import asyncio
import unittest
import os

from gws.settings import Settings
from gws.model import *
from gws.file import File
from gws.store import LocalFileStore
from gws.unittest import GTest
  
class TestFile(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        LocalFileStore.remove_all_files(ignore_errors=True)
        File.drop_table()
        tables = ( Config, Process, Protocol, Experiment, Study, User, Activity, ProgressBar, )
        GTest.drop_tables(tables)
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        tables = ( Config, Process, Protocol, Experiment,  Study, User, Activity, ProgressBar, )
        GTest.drop_tables(tables)
        pass
    
    def test_file(self):
        fs = LocalFileStore()
        f = fs.create_file(name="my_file.txt")
        f.save()
        self.assertTrue(f.is_saved())
        
        f.write("Hi.\n")
        f.write("My name is John")
        
        text = f.read()
        self.assertTrue(text, "Hi.\nMy name is John")
        self.assertTrue(f.verify_hash())