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

cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(cdir,"/gws"))
import gws.settings as settings
from gws.prism.model import DbManager

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", nargs="?", action='store', type=str, help="run tests using name pattern")
    #parser.add_argument("-r", "--run", action='store_true', help="run server")
    args = parser.parse_args()

    if args.test:
        if args.test == "*":
            args.test = "test*"
        if args.test == "all":
            args.test = "test*"

        settings.is_test = True
        DbManager.connect_db()
        loader = unittest.TestLoader()
        test_suite = loader.discover(".", pattern=args.test+"*.py")
        test_runner = unittest.TextTestRunner()
        test_runner.run(test_suite)
        DbManager.close_db()