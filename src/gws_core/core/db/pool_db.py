

from multiprocessing.pool import Pool
from typing import Set, Type

from gws_core.core.db.db_manager import AbstractDbManager


class PoolDb(Pool):
    """
    Use this class to create a pool of processes that can use the db (in parallel).

    Class that extends multiprocessing.pool to allow to use the db in the
    sub processes. It clears the db connection before and after the pool.



    :param Pool: _description_
    :type Pool: _type_
    """

    def __enter__(self):
        db_managers = self.get_dbs()

        for db_manager in db_managers:
            db_manager.close_db()
            db_manager.connect_db()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        db_managers = self.get_dbs()

        for db_manager in db_managers:
            db_manager.close_db()
        return super().__exit__(exc_type, exc_val, exc_tb)

    def get_dbs(self) -> Set[Type[AbstractDbManager]]:
        return AbstractDbManager.inheritors()
