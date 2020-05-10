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
from gws.settings import Settings

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", nargs="?", action='store', type=str, help="run tests using name pattern")
    parser.add_argument("-d", "--db", nargs="?", action='store', type=str, help="Database file name")
    args = parser.parse_args()

    settings = Settings.retrieve()

    if args.test:
        if args.test == "*":
            args.test = "test*"
        if args.test == "all":
            args.test = "test*"

        settings.data["db_name"] = 'db_test.sqlite3'
        settings.data["is_test"] = True

        if args.db:
            settings.data["db_name"] = args.db

        settings.save()

        #print('------')
        # print(settings.data)
        # print(settings.data)
        #print(settings.db_path)

        from gws.prism.model import DbManager
        DbManager.connect_db()
        loader = unittest.TestLoader()
        test_suite = loader.discover(".", pattern=args.test+"*.py")
        test_runner = unittest.TextTestRunner()
        test_runner.run(test_suite)
        DbManager.close_db()
    
    if args.db:
        settings.data["db_name"] = args.db
        settings.save()