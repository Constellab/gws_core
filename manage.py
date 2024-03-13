

import os
import sys

if 'gws_core' not in sys.modules:
    core_lib_path = "/lab/user/bricks/gws_core/src"
    if not os.path.exists(core_lib_path):
        core_lib_path = "/lab/.sys/bricks/gws_core/src"
        if not os.path.exists(core_lib_path):
            raise Exception("Cannot find gws_core brick")
    sys.path.insert(0, core_lib_path)


if __name__ == "__main__":
    from gws_core import manage
    __cdir__ = os.path.dirname(os.path.abspath(__file__))
    manage.start_app(__cdir__)
