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
cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(cdir,"./gws"))

# set settings
from gws.settings import Settings

# ... set setting here ...

from gws.prism.manage import manage

if __name__ == "__main__":
    manage()