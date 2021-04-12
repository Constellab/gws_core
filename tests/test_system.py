
import unittest
from gws.system import SysProc

class TestSysProc(unittest.TestCase):
    
    def test_sysproc(self):
        
        sp = SysProc()
        sp.popen(["echo 1 "])
        