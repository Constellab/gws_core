# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import tempfile
import subprocess

from gws.utils import slugify
from gws.system import SysProc

from .base import BaseS3

class Swift(BaseS3):

    url = "https://storage.uk.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/public"
    user="user-3Knk5z4CvP9D"
    password="fVBdvkGrCPj5VpSdbm5FjguF8gCDzjcf"

    def create(self, repo: str):
        cmd = [
            f"export ST_AUTH={self.url}",
            f"export ST_USER={self.user}",
            f"export ST_KEY={self.password}",
            f"swift post {repo}"
        ]
        SysProc.popen(
            " && ".join(cmd),
            shell=True,
            stdout=subprocess.PIPE
        )

    def post(self, repo: str, file_path: str):
        cmd = [
            f"export ST_AUTH={self.url}",
            f"export ST_USER={self.user}",
            f"export ST_KEY={self.password}",
            f"swift upload {repo} {file_path}",
        ]
        SysProc.popen(
            " && ".join(cmd),
            shell=True,
            stdout=subprocess.PIPE
        )

    def get(self):
        pass
