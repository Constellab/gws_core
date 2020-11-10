# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os

__cdir__ = os.path.dirname(os.path.abspath(__file__))
def set_path(rel_gws_path):
    for _ in range(0,10):
        rel_gws_path = os.path.join("../", rel_gws_path)
        abs_gws_path = os.path.join(__cdir__, rel_gws_path)
        if os.path.exists(abs_gws_path):
            sys.path.append(abs_gws_path)
            return True

is_set = set_path("./gws/bricks/gws") or set_path("./.gws/bricks/gws")
if not is_set:
    raise Exception("Cannot find the base gws brick")

from gws import runner
from gws.manage import load_settings

if __name__ == "__main__":
    __cdir__ = os.path.dirname(os.path.abspath(__file__))
    load_settings(__cdir__)
    runner.run()