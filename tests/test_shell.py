
import asyncio
import unittest
import os

from gws.settings import Settings
from gws.file import File
from gws.model import Resource, Study, User
from gws.shell import EasyShell, CondaShell
from gws.unittest import GTest

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

class CondaEcho(CondaShell):
    pass


class TestShell(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Echo.drop_table()
        Study.drop_table()
        User.drop_table()
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        Echo.drop_table()
        Study.drop_table()
        User.drop_table()
        pass
    
    def test_shell(self):        
        proc = Echo(instance_name="shell")
        proc.set_param("name", "Jhon Doe")
        e = proc.create_experiment(study=GTest.study, user=GTest.user)
        
        def _on_end(*args, **kwargs):
            res = proc.output['stdout']
            self.assertEqual(res.data["out"], "Jhon Doe\n")
            
            
        e.on_end(_on_end)
        asyncio.run( e.run(user=GTest.user) )