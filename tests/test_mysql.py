# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import unittest

from gws_core import File, FileModel, FileService, GTest, MySQLService
from gws_core.core.db.db_manager import DbManager


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

        if DbManager.is_sqlite_engine():
            print("SQLite3 db detected: exit test, OK!")
            return

        # insert data in comment table
        f = File()
        f.path = "./oui"
        file_model: FileModel = FileService.create_file_model(file=f)

        c = file_model.add_comment("The sky is blue")
        file_model.add_comment("The sky is blue and the ocean is also blue", reply_to=c)
        file_model.save()

        # dump db
        output_file = MySQLService.dump_db(
            "test_gws", force=True, wait=True)
        self.assertTrue(os.path.exists(output_file))

        GTest.drop_tables()
        self.assertFalse(FileModel.table_exists())

        # load db
        MySQLService.load_db(
            "test_gws", local_file_path=output_file, force=True, wait=True)
        self.assertTrue(FileModel.table_exists())

    def test_db_drop(self):
        pass
