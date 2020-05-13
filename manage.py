#
# Core GWS manage module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import sys
import os
import unittest
import argparse
import uvicorn

# load prism module
__cdir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(__cdir__,"./"))        # -> load gws tests
sys.path.append(os.path.join(__cdir__,"./src"))     # -> load gws module

# set settings
from gws.settings import Settings

Settings.add_statics({
    '/static/gws'   : os.path.join(__cdir__, './src/static/gws')
})

Settings.init(dict(
    app_dir         = __cdir__,
    app_host        = 'localhost',
    app_port        = 3000,
    db_dir          = __cdir__,
    db_name         = 'db.sqlite3',     # ':memory:'
    is_test         = False,
))

from gws.prism.manage import manage

if __name__ == "__main__":
    manage()