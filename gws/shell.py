# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional
from gws.model import Process
from gws.file import File

class ShellProcess(Process):
    input_specs = {'file' : (File, None,)}
    output_specs = {'file' : File}
    config_specs = {
        'binary_file_path': {"type": str, "default": None, 'description': "File path"},
        'command': {"type": 'str', "default": '', "description": "Parameter"},
    }
    
    async def task(self):
        pass

class CondaProcess(ShellProcess):
    pass

