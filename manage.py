# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import sys

if 'gws_core' not in sys.modules:
    __cdir__ = os.path.dirname(os.path.abspath(__file__))

    def set_path(rel_gws_path):
        for _ in range(0, 10):
            rel_gws_path = os.path.join("../", rel_gws_path)
            abs_gws_path = os.path.join(__cdir__, rel_gws_path)
            if os.path.exists(abs_gws_path):
                sys.path.append(abs_gws_path)
                return True

    is_set = set_path("./.core/bricks/gws_core/src") or set_path("./core/bricks/gws_core/src")
    if not is_set:
        raise Exception("Cannot find the base gws brick")

from gws_core import runner
from gws_core.manage import load_settings

if __name__ == "__main__":
    __cdir__ = os.path.dirname(os.path.abspath(__file__))
    load_settings(__cdir__)
    runner.run()
