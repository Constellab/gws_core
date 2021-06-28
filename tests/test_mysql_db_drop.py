# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

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
        #GTest.drop_tables()
        pass

    def test_db_drop(self):
        GTest.print("Test database drop")

        # insert data in comment table
        f = File(path="./oui")
        c = f.add_comment("The sky is blue")
        f.add_comment("The sky is blue and the ocean is also blue", reply_to=c)
        f.save()
        
        # drop db
        proc = MySQLDrop()
        e = proc.create_experiment(user=GTest.user, study=GTest.study)

        def _on_end(*args, **kwargs):
            self.assertFalse(File.table_exists())

        e.on_end(_on_end)
        asyncio.run( e.run() )

        n = 0
        while not e.is_finished:
            print("Waiting 3 secs for experiment to ...")
            time.sleep(3)
            if n == 10:
                raise Error("The experiment queue is not empty")
            n += 1

