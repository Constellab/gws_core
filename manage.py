# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os

gws_path = "./gws/bricks/gws"
is_loaded  = False
for k in range(0,10):
    gws_path = os.path.join("../", gws_path)
    if os.path.exists(gws_path):
        sys.path.append(gws_path)
        is_loaded  = True
        break

if not is_loaded:
    raise Exception("Cannot find the base gws brick")

from gws import runner
from gws.manage import load_settings

if __name__ == "__main__":
    __cdir__ = os.path.dirname(os.path.abspath(__file__))
    load_settings(__cdir__)
    runner.run()