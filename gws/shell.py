# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import tempfile
import re
import subprocess

from typing import Optional
from gws.model import Process
from gws.file import File
from gws.settings import Settings
from gws.file import FileStore
from gws.controller import Controller

class Shell(Process):
    input_specs = {}
    output_specs = {}
    config_specs = {}
    
    _out_type = "text"
    
    def build_command(self) -> str:
        return ""

    def after_command(self, stdout: str=None, tmp_dir: str=None):
        pass
    
    async def task(self):
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            cmd = self.build_command()

            stdout = subprocess.check_output( 
                cmd,
                text = True if self._out_type == "text" else False,
                cwd=tmp_dir
            )
            
            self.data['cmd'] = cmd 
            self.after_command(stdout=stdout, tmp_dir=tmp_dir)
            
            for k in self.output:
                f = self.output[k]
                if isinstance(f, File):
                    f.move_to_store()
            
class EasyShell(Shell):
    
    _cmd: list = None
    
    def build_command(self) -> str:
        
        cmd = self._cmd
        
        for i in range(0, len(self._cmd)):
            
            cmd_part = cmd[i]
            for k in self.config.params:
                param = self.get_param(k)
                if isinstance(param, str):
                    cmd_part = cmd_part.replace(f"{{param:{k}}}", param)

            for k in self.input:
                file = self.input[k]
                cmd_part = cmd_part.replace(f"{{in:{k}}}", file.path)

            cmd[i] = cmd_part
            
        return cmd