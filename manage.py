# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import sys

if 'gws_core' not in sys.modules:
    core_lib_path = "/lab/user/bricks/gws_core/src"
    if not os.path.exists(core_lib_path):
        core_lib_path = "/lab/user/bricks/.lib/gws_core/src"
        if not os.path.exists(core_lib_path):
            raise Exception("Cannot find gws_core brick")
    sys.path.insert(0, core_lib_path)

from gws_core import manage, runner

if __name__ == "__main__":
    __cdir__ = os.path.dirname(os.path.abspath(__file__))
    manage.load_settings(__cdir__)
    runner.run()
