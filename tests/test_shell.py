
import asyncio
import unittest
import os

from gws.settings import Settings
from gws.file import File
from gws.model import Resource
from gws.shell import EasyShell, CondaShell

class Echo(EasyShell):
    input_specs = {}
    output_specs = {'stdout': (Resource, )}
    config_specs = {
        'name': {"type": str, "default": None, 'description': "The name to echo"},
        'save_stdout': {"type": bool, "default": False, 'description': "True to save the command output text. False otherwise"},
    }
    
    _cmd: list = ['echo', '{param:name}']
    
    def after_command(self, stdout: str=None, tmp_dir: str=None):
        res = Resource()
        res.data["out"] = stdout
        self.output["stdout"] = res

class Echo(CondaShell):
    input_specs = {}
    output_specs = {'stdout': (Resource, )}
    config_specs = {
        'name': {"type": str, "default": None, 'description': "The name to echo"},
        'save_stdout': {"type": bool, "default": False, 'description': "True to save the command output text. False otherwise"},
    }
    
    _cmd: list = ['echo', '{param:name}']
    
    def after_command(self, stdout: str=None, tmp_dir: str=None):
        res = Resource()
        res.data["out"] = stdout
        self.output["stdout"] = res

class TestShell(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass
    
    def test_shell(self):
        
        proc = Echo(instance_name="shell")
        proc.set_param("name", "Jhon Doe")
        e = proc.create_experiment()
        
        def _on_end(*args, **kwargs):
            res = proc.output['stdout']
            self.assertEqual(res.data["out"], "Jhon Doe\n")
            
            
        e.on_end(_on_end)
        
        asyncio.run( e.run() )
        pass