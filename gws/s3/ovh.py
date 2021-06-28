# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import tempfile
import subprocess

from gws.shell import Shell
from gws.file import File
from gws.settings import Settings
from gws.utils import slugify
from gws.system import SysProc

from .base import BaseS3

class OVHS3(BaseS3):

    url = "https://storage.uk.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/public"

    def create(self, repo: str):
        repo = slugify(repo)
        cmd = [
            "swift",
            "post",
            os.path.join(self.url, repo)
        ]

        SysProc.popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE
        )

    def post(self, repo: str):
        pass

    def get(self):
        pass
