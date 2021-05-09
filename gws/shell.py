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
    """
    Shell class. 
    
    This class is a proxy to run user shell commands through the Python method `subprocess.run`.
    """
    
    input_specs = {}
    output_specs = {}
    config_specs = {}
    
    _out_type = "text"
    _tmp_dir = None
    _shell = False
    
    def build_command(self) -> list:
        """
        This method builds the command to execute.
        
        :return: The list of arguments used to build the final command in the Python method `subprocess.run`
        :rtype: `list`
        """
        
        return [""]
    
    def _format_command(self, user_cmd) -> (list, str, ):
        """
        Format the final shell command
        
        :param stdout: The final command
        :param type: `list`, `str`
        """
        
        return user_cmd

    def gather_outputs(self, stdout: str=None):
        """
        This methods gathers the results of the shell process. It must be overloaded by subclasses.
        
        It must be overloaded to capture the standard output (stdout) and the 
        output files generated in the current working directory (see `gws.Shell.cwd`)
        
        :param stdout: The standard output of the shell process
        :param type: `str`
        """
        
        pass
    
    @property
    def cwd(self):
        """
        The temporary working directory where the shell command is executed. 
        This directory is removed at the end of the process

        :return: a file-like object built with `tempfile.TemporaryDirectory`
        :rtype: `file object`
        """
        
        if self._tmp_dir is None:
            self._tmp_dir = tempfile.TemporaryDirectory()
 
        return self._tmp_dir
    
    async def task(self): 
        """
        Task entrypoint
        """
        
        try:
            user_cmd = self.build_command()
            cmd = self._format_command(user_cmd=user_cmd)

            if isinstance(cmd, list):
                for k in range(0,len(cmd)):
                    cmd[k] = str(cmd[k])

            if not os.path.exists(self.cwd.name):
                os.makedirs(self.cwd.name)

            proc = subprocess.run( 
                cmd,
                text = True if self._out_type == "text" else False,
                cwd=self.cwd.name,
                shell=self._shell,
                stdout=subprocess.PIPE
            )
            
            self.data['cmd'] = cmd 
            self.gather_outputs(stdout=proc.stdout)

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

            
class CondaShell(Shell):
    _shell = True
    def _format_command(self, user_cmd) -> list:
        if isinstance(user_cmd, list):
            for k in range(0,len(user_cmd)):
                user_cmd[k] = str(user_cmd[k])
                    
            user_cmd = ' '.join(user_cmd)
        
        cmd = 'bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate base && ' + user_cmd + '"'
        return cmd

    
class EasyShell(Shell):
    _shell = False
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