# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
import os
import asyncio
import unittest
from gws.db.mysql import MySQLDump
from gws.unittest import GTest
from gws.file import File

class TestDb(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()
        
    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()
        pass

    def test_db_dump(self):
        GTest.print("Test database dump")

        # insert data in comment table
        f = File(path="./oui")
        c = f.add_comment("The sky is blue")
        f.add_comment("The sky is blue and the ocean is also blue", reply_to=c)
        f.save()
        
        # dump db
        dump = MySQLDump()
        dump.run()
        time.sleep(1)

        print("Waiting for dump to finish ...")
        n = 0
        while dump.is_in_progress():
            time.sleep(1)
            n = n+1
            if n == 10:
                break
        print("Done!")

        print(dump.output_file)
        self.assertTrue(os.path.exists(dump.output_file))
