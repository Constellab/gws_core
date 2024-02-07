# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from multiprocessing import Pool
from unittest import TestCase

from peewee import CharField

from gws_core.core.db.pool_db import PoolDb
from gws_core.core.model.model import Model


class TestTable(Model):

    id = CharField(primary_key=True, max_length=36)
    text = CharField()

    _table_name = 'test_table'


def _simple_select(_):
    list(TestTable.select())


# test_pool_multi
class TestPoolMulti(TestCase):

    # clean the table and db connection after the test (required if other tests are run after)
    @classmethod
    def tearDownClass(cls):
        TestTable.get_db_manager().close_db()
        TestTable.drop_table()

    def test_pool_multi(self):
        """ We test that the pool reset the db so sub the processes can use it
        So we open the db before the pool and close it after"""
        TestTable.drop_table()
        TestTable.create_table()
        for i in range(0, 1000):
            TestTable.create(id=str(i), text=f'text_{i}')

        # force opening the db before the pool
        list(TestTable.select())
        self._working_pool()

        list(TestTable.select())
        self.assertRaises(Exception, self._not_working_pool)

    def _working_pool(self):
        i = 0
        with PoolDb(processes=4) as pool:
            for _ in pool.map(_simple_select, list(range(0, 16))):
                i += 1

    def _not_working_pool(self):
        i = 0
        with Pool(processes=4) as pool:
            for _ in pool.map(_simple_select, list(range(0, 16))):
                i += 1
