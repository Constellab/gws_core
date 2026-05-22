import os
from collections.abc import Callable
from multiprocessing import Process

from gws_core.core.db.abstract_db_manager import AbstractDbManager
from gws_core.core.utils.logger import Logger


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

    def __init__(
        self,
        group=None,
        target: Callable | None = None,
        name: str | None = None,
        args: tuple = (),
        kwargs: dict | None = None,
        *,
        daemon: bool | None = None,
    ):
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
        super().__init__(
            group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon
        )

    def run(self):
        """
        Override the run method to reset db connections before running the target function.

        On completion the subprocess exits via ``os._exit`` instead of returning
        normally. Returning normally lets the CPython interpreter run its full
        shutdown sequence (atexit handlers, thread joins, C-extension
        finalizers); if any of those faults, ``multiprocessing`` reports a
        non-zero exit code even though the target succeeded and committed its
        work. ``os._exit`` skips that shutdown, so the exit code reflects only
        whether the target itself failed.
        """
        # Reset db connections in the subprocess
        AbstractDbManager.reconnect_dbs()

        target_error: BaseException | None = None
        try:
            super().run()
        except BaseException as err:
            target_error = err
        finally:
            # Clean up db connections after the process finishes. This must
            # never fail the subprocess: the target has already completed and
            # committed its work by this point.
            try:
                AbstractDbManager.close_dbs()
            except Exception as err:
                Logger.error(f"Error while closing db connections in ProcessDb: {err}")

        os._exit(1 if target_error is not None else 0)
