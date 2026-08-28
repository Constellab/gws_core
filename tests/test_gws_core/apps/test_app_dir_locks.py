import os
import threading
import time
from typing import cast
from unittest import TestCase
from unittest.mock import MagicMock

from gws_core.apps.app_dir_locks import AppDirLocks
from gws_core.apps.reflex.reflex_process import ReflexProcess
from gws_core.core.utils.settings import Settings
from gws_core.impl.shell.shell_proxy import ShellProxy


# test_app_dir_locks
class TestAppDirLocks(TestCase):
    """Per-app-folder lock serializing reflex frontend builds (issue #103)."""

    def test_same_path_same_lock(self):
        temp_dir = Settings.make_temp_dir()
        lock_a = AppDirLocks.get_lock(temp_dir)
        # different spelling of the same path
        lock_b = AppDirLocks.get_lock(os.path.join(temp_dir, ".", ""))
        self.assertIs(lock_a, lock_b)

        other_dir = Settings.make_temp_dir()
        self.assertIsNot(AppDirLocks.get_lock(other_dir), lock_a)

    def test_build_frontend_is_serialized_per_app_folder(self):
        """N concurrent _build_frontend calls on the same app folder never overlap."""
        app_folder = Settings.make_temp_dir()

        app = MagicMock()
        app.get_app_folder.return_value = app_folder

        concurrent = 0
        max_concurrent = 0
        counter_lock = threading.Lock()

        def fake_build_locked(shell_proxy, env, app) -> str:
            nonlocal concurrent, max_concurrent
            with counter_lock:
                concurrent += 1
                max_concurrent = max(max_concurrent, concurrent)
            time.sleep(0.05)
            with counter_lock:
                concurrent -= 1
            return "/fake/build/path"

        # bypass __init__ (needs a full AppInstance): only the locking wiring is under test
        process = ReflexProcess.__new__(ReflexProcess)
        process._build_frontend_locked = fake_build_locked  # type: ignore[method-assign]

        errors: list[Exception] = []

        def build():
            try:
                result = process._build_frontend(cast(ShellProxy, None), {}, app)
                if result != "/fake/build/path":
                    errors.append(Exception(f"unexpected result {result}"))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=build) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        self.assertEqual(errors, [])
        self.assertEqual(max_concurrent, 1)
