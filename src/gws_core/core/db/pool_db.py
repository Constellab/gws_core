from multiprocessing.pool import Pool

from gws_core.core.db.abstract_db_manager import AbstractDbManager


class PoolDb(Pool):
    """
    Use this class to create a pool of processes that can use the db (in parallel).

    Class that extends multiprocessing.pool to allow to use the db in the
    sub processes. It clears the db connection before and after the pool.



    :param Pool: _description_
    :type Pool: _type_
    """

    def __enter__(self):
        AbstractDbManager.reconnect_dbs()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        AbstractDbManager.close_dbs()
        return super().__exit__(exc_type, exc_val, exc_tb)
