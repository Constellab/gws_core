# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
import os
import asyncio
import unittest
from gws.db.mysql import MySQLDump, MySQLLoad
from gws.service.mysql_service import MySQLService
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

    def test_db_dump_load(self):
        GTest.print("MySQL dump and load")
        
        if File.get_db_manager().is_sqlite_engine():
            print("SQLite3 db detected: exit test, OK!")
            return

        # insert data in comment table
        f = File(path="./oui")
        c = f.add_comment("The sky is blue")
        f.add_comment("The sky is blue and the ocean is also blue", reply_to=c)
        f.save()
        
        # dump db
        output_file = MySQLService.dump_db("gws", force=True, wait=True)
        self.assertTrue(os.path.exists(output_file))

        GTest.drop_tables()
        self.assertFalse(File.table_exists())

        # load db
        MySQLService.load_db("gws", local_file_path=output_file, force=True, wait=True)
        self.assertTrue(File.table_exists())

    def test_db_drop(self):
        pass