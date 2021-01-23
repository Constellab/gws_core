# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import tempfile

from typing import Optional
from gws.model import Process
from gws.file import File
from gws.settings import Settings
from gws.file import FileStore
from gws.controller import Controller

class ShellProcess(Process):
    input_specs = {'file' : (File, None,)}
    output_specs = {'file' : (File, None,)}
    config_specs = {
        'bin': {"type": str, "default": None, 'description': "Binary file to call (eg. scp, cp, ...)"},
        'save_stdout': {"type": str, "default": False, 'description': "True to save the command output text. False otherwise"},
    }
    
    def build_command(self) -> list:
        cmd = self.get_param('command')
        param = []
        for k in self.config.params:
            param.append( k + " " + str(self.config.params[k]) )
        return [ cmd ] + param
    
    
    def after_command(self, output_dir):
        pass
    
    async def task(self):
        
        with tempfile.TemporaryDirectory() as output_dir:
            cmd = self.build_command()
            
            output_text = subprocess.check_output( 
                *cmd,
                stderr=subprocess.STDOUT,
                cwd=output_dir
            )
            
            if self.get_param('save_stdout'):
                self.data['stdout'] = output_text
                
            self.after_command(output_dir)
            #... 

class CppProcess(Process):
    pass

class CondaProcess(ShellProcess):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__install_venv()
    
    def venv_dir(cls):
        settings = Controller.get_settings()
        venv_dir = settings.get_venv_dir()
        return os.path.join(venv_dir, cls.fclassname(slugify=True))
        
    @classmethod
    def __install_venv(cls):
        venv_dir = cls.venv_dir()
        if os.path.exists(venv_dir):
            os.makedirs(venv_dir)
         
        