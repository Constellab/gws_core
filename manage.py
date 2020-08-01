# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os

sys.path.append(os.path.join("./"))
from gws import runner
from gws.manage import load_settings

if __name__ == "__main__":
    __cdir__ = os.path.dirname(os.path.abspath(__file__))
    load_settings(__cdir__)
    runner.run()