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
from gws.file import FileStore, LocalFileStore
from gws.controller import Controller
from gws.logger import Error

class Shell(Process):
    input_specs = {}
    output_specs = {}
    config_specs = {}
    
    _out_type = "text"
    _tmp_dir = None
    
    __activate_env_command = []
    
    def build_command(self) -> (list):
        return [""]

    def after_command(self, stdout: str=None):
        pass
    
    @property
    def cwd(self):
        if self._tmp_dir is None:
            self._tmp_dir = tempfile.TemporaryDirectory()
 
        return self._tmp_dir
    
    async def task(self):
        try:
            cmd = [
                *self.__activate_env_command,
                *self.build_command()
            ]

            stdout = subprocess.check_output( 
                cmd,
                text = True if self._out_type == "text" else False,
                cwd=self.cwd.name
            )
                
            self.data['cmd'] = cmd 
            self.after_command(stdout=stdout)
            
            for k in self.output:
                f = self.output[k]
                if isinstance(f, File):
                    f.move_to_default_store()
            
            self._tmp_dir.cleanup()
            self._tmp_dir = None
        except subprocess.CalledProcessError as err:
            self._tmp_dir.cleanup()
            self._tmp_dir = None
            Error("Shell","task", f"An error occured while running the binary in shell process. Error: {err}")
        
        except Exception as err:
            Error("Shell","task", f"An error occured while running shell process. Error: {err}")

            
class CondaShell(Process):
    __activate_env_command = [ "bash", "-c",  "conda activate", "&&" ]


class EasyShell(Shell):
    
    _cmd: list = None
    
    def build_command(self) -> list:
        
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