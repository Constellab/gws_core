

import os
import sys

user_bricks_folder = os.path.join('/lab', 'user', 'bricks')
sys_bricks_folder = os.path.join('/lab', '.sys', 'bricks')
app_folder = os.path.join('/lab', '.sys', 'app')


def activate():

    if 'gws_core' not in sys.modules:
        core_lib_path = os.path.join(user_bricks_folder, 'gws_core', 'src')
        if not os.path.exists(core_lib_path):
            core_lib_path = os.path.join(sys_bricks_folder, 'gws_core', 'src')
            if not os.path.exists(core_lib_path):
                raise Exception("Cannot find gws_core brick")
        sys.path.insert(0, core_lib_path)

    from gws_core import manage
    manage.start_notebook(str(app_folder))
    return str(app_folder)
