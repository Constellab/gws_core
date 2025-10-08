

from multiprocessing import Process
from typing import Any, Callable, Set, Type

from gws_core.core.db.db_manager import AbstractDbManager


class ProcessDb(Process):
    """
    Use this class to create a background process that can use the db.

    Class that extends multiprocessing.Process to allow to use the db in the
    subprocess. It clears the db connection before starting the process.

    This is useful when you want to run a task in the background without waiting
    for it to finish, but the task needs a clean database connection.

    Example:
        def my_task(arg1, arg2):
            # This function will run in a separate process with clean db connection
            results = MyModel.select()
            # ... do work ...

        # Start the process
        process = ProcessDb(target=my_task, args=(value1, value2))
        process.start()

        # Optionally wait for it to finish
        process.join()

    :param Process: multiprocessing.Process
    :type Process: type
    """

    def __init__(self, group=None, target: Callable = None, name: str = None,
                 args: tuple = (), kwargs: dict = None, *, daemon: bool = None):
        """
        Initialize the ProcessDb

        :param group: reserved for future extension
        :param target: the callable object to be invoked by the run() method
        :type target: Callable
        :param name: the process name
        :type name: str
        :param args: the argument tuple for the target invocation
        :type args: tuple
        :param kwargs: a dictionary of keyword arguments for the target invocation
        :type kwargs: dict
        :param daemon: whether the process is a daemon
        :type daemon: bool
        """
        if kwargs is None:
            kwargs = {}
        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)

    def run(self):
        """
        Override the run method to reset db connections before running the target function
        """
        # Reset db connections in the subprocess
        db_managers = self.get_dbs()
        for db_manager in db_managers:
            db_manager.close_db()
            db_manager.connect_db()

        try:
            # Run the target function
            super().run()
        finally:
            # Clean up db connections after the process finishes
            for db_manager in db_managers:
                db_manager.close_db()

    def get_dbs(self) -> Set[Type[AbstractDbManager]]:
        """Get all database managers

        :return: set of database manager classes
        :rtype: Set[Type[AbstractDbManager]]
        """
        return AbstractDbManager.inheritors()
