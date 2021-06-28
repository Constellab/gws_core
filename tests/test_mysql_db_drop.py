# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
import os
import asyncio
import unittest
from gws.db.mysql import MySQLDrop
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

    def test_db_drop(self):
        GTest.print("Test database drop")

        # insert data in comment table
        f = File(path="./oui")
        c = f.add_comment("The sky is blue")
        f.add_comment("The sky is blue and the ocean is also blue", reply_to=c)
        f.save()
        
        # drop db
        drop = MySQLDrop()
        drop.run()

        print("Waiting for db drop to finish ...")
        n = 0
        while not drop.is_ready():
            time.sleep(3)
            if n == 10:
                break
            n += 1
        print("Done!")

        self.assertFalse(File.table_exists())
