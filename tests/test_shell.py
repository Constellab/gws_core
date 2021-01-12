
import asyncio
import unittest
import os

from gws.settings import Settings
from gws.file import File
from gws.shell import ShellProcess

  
class TestShell(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass
    
    def test_shell(self):
        
        proc = ShellProcess()
        
        f_t = proc.input_specs['file']
        
        print(f_t)