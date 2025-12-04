from threading import Thread

from gws_core.core.db.abstract_db_manager import AbstractDbManager


class ThreadDb(Thread):
    """
    Use this class to create a long-running thread that can use the db.

    Class that extends threading.Thread to allow to use the db in the thread.
    It resets the db connection once when the thread starts, not on every operation.

    This is useful for background threads that need to continuously access the database,
    like monitoring or periodic tasks.

    Example:
        def my_continuous_task():
            while True:
                # This function runs in a separate thread with clean db connection
                results = MyModel.select()
                # ... do work ...
                time.sleep(interval)

        # Start the thread
        thread = ThreadDb(target=my_continuous_task)
        thread.daemon = True
        thread.start()

    :param Thread: threading.Thread
    :type Thread: type
    """

    def __init__(
        self,
        group=None,
        target=None,
        name: str = None,
        args: tuple = (),
        kwargs: dict = None,
        daemon: bool = None,
    ):
        """
        Initialize the ThreadDb

        :param group: reserved for future extension
        :param target: the callable object to be invoked by the run() method
        :param name: the thread name
        :type name: str
        :param args: the argument tuple for the target invocation
        :type args: tuple
        :param kwargs: a dictionary of keyword arguments for the target invocation
        :type kwargs: dict
        :param daemon: whether the thread is a daemon
        :type daemon: bool
        """
        if kwargs is None:
            kwargs = {}
        super().__init__(
            group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon
        )

    def run(self):
        """
        Override the run method to reset db connections once before running the target function
        """
        # Reset db connections in the thread (only once at startup)
        AbstractDbManager.reconnect_dbs()

        try:
            # Run the target function
            super().run()
        finally:
            # Clean up db connections when the thread exits
            AbstractDbManager.close_dbs()
