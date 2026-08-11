import os
import threading


class AppDirLocks:
    """Registry of re-entrant locks keyed by app folder path.

    Several instances of the same app share one source folder (the app folder holds
    `.web`, `node_modules`, `assets`, ...), and operations like the Reflex frontend
    build mutate it heavily. This registry provides one lock per folder so those
    operations can be serialized.

    A `threading` lock is sufficient because all app starts run as threads of the
    single server process (see `AppProcess.start_app_async`). If app starts ever span
    several processes, this must be replaced by a cross-process lock (`fcntl.flock`).
    """

    _locks: dict[str, threading.RLock] = {}
    _registry_lock = threading.Lock()

    @classmethod
    def get_lock(cls, dir_path: str) -> threading.RLock:
        """Get (or create) the lock associated with a directory.

        :param dir_path: directory to lock; resolved so different spellings of the
            same path share one lock
        :type dir_path: str
        :return: the re-entrant lock for this directory
        :rtype: threading.RLock
        """
        key = os.path.realpath(dir_path)
        with cls._registry_lock:
            if key not in cls._locks:
                cls._locks[key] = threading.RLock()
            return cls._locks[key]
