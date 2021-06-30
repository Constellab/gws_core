# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
import os
import asyncio
import unittest
from gws.db.mysql import MySQLDump, MySQLLoad
from gws.unittest import GTest
from gws.file import File

class TestMySQLDumpLoad(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()
        
    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()
        pass

    def test_db_dump_load(self):
        GTest.print("Test MySQL db dump & load")
        
        if File.get_db_manager().is_sqlite_engine():
            print("SQLite3 db detected: exit test, OK!")
            return

        # insert data in comment table
        f = File(path="./oui")
        c = f.add_comment("The sky is blue")
        f.add_comment("The sky is blue and the ocean is also blue", reply_to=c)
        f.save()
        
        # dump db
        dump = MySQLDump()
        dump.run(force=True, wait=True)
        print(dump.output_file)
        self.assertTrue(os.path.exists(dump.output_file))

        GTest.drop_tables()
        self.assertFalse(File.table_exists())

        # load db
        load = MySQLLoad()
        load.run(force=True, wait=True)
        self.assertTrue(File.table_exists())

    def test_db_drop(self):
        pass