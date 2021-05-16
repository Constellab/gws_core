# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import unittest
from gws.system import SysProc

class TestSysProc(unittest.TestCase):
    
    def test_sysproc(self):
        sp = SysProc()
        sp.popen(["echo 1 "])
        