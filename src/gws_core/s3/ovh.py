# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess

from ..core.model.sys_proc import SysProc
from ..core.utils.util import Util
from .base import BaseS3


class OVHS3(BaseS3):

    url = "https://storage.uk.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/public"

    def create(self, repo: str):
        repo = Util.slugify(repo)
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
