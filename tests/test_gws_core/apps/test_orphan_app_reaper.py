import os
import subprocess
import sys
import time
from unittest import TestCase

import psutil
from gws_core.apps.app_process import AppProcess
from gws_core.core.model.sys_proc import SysProc


def _wait_gone(pid: int, timeout: float = 5.0) -> bool:
    """Return True if `pid` is gone (or a zombie) within `timeout` seconds."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not psutil.pid_exists(pid):
            return True
        try:
            if psutil.Process(pid).status() == psutil.STATUS_ZOMBIE:
                return True
        except psutil.NoSuchProcess:
            return True
        time.sleep(0.05)
    return False


# test_orphan_app_reaper
class TestOrphanAppReaper(TestCase):
    """Reaping of orphaned app child processes at boot (issue #97).

    Spawns a real, detached (own process group) child that carries the app marker env
    var — the same shape as a leaked streamlit/reflex process — and checks that
    ``SysProc.kill_orphan_app_processes`` finds and kills it by marker, while leaving a
    marker-less process untouched.
    """

    _spawned: list[subprocess.Popen]

    def setUp(self) -> None:
        self._spawned = []

    def tearDown(self) -> None:
        # Backstop: make sure no test child survives the test.
        for proc in self._spawned:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, 9)
            except (ProcessLookupError, OSError):
                pass

    def _spawn_sleeper(self, marker_value: str | None) -> subprocess.Popen:
        """Spawn a detached `python -c 'sleep'` child.

        :param marker_value: value to set for the app marker env var, or None to leave it unset
            (simulating an unrelated, non-app process).
        """
        env = dict(os.environ)
        if marker_value is not None:
            env[AppProcess.APP_ID_ENV_VAR] = marker_value
        else:
            env.pop(AppProcess.APP_ID_ENV_VAR, None)

        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            env=env,
            start_new_session=True,  # own process group, like a real app child
        )
        self._spawned.append(proc)
        # Give the child a moment to be visible in the process table with its env.
        time.sleep(0.2)
        return proc

    def test_reaps_marked_process(self) -> None:
        """Boot reaper: every marked process is killed (nothing is tracked at boot)."""
        orphan = self._spawn_sleeper(marker_value="test-orphan-app")

        killed = SysProc.kill_orphan_app_processes(
            AppProcess.APP_ID_ENV_VAR, port_band=range(0, 0)
        )

        self.assertIn(orphan.pid, killed)
        self.assertTrue(_wait_gone(orphan.pid), "orphan process should be killed")

    def test_ignores_unmarked_process(self) -> None:
        """A process without the marker is never reaped."""
        other = self._spawn_sleeper(marker_value=None)

        killed = SysProc.kill_orphan_app_processes(
            AppProcess.APP_ID_ENV_VAR, port_band=range(0, 0)
        )

        self.assertNotIn(other.pid, killed)
        self.assertFalse(_wait_gone(other.pid, timeout=1.0), "unmarked process must survive")

    def test_find_marked_processes_reports_marker_value(self) -> None:
        """find_marked_processes maps pid -> marker value, so callers can select by app id."""
        app_a = self._spawn_sleeper(marker_value="app-a")
        app_b = self._spawn_sleeper(marker_value="app-b")

        marked, _denied = SysProc.find_marked_processes(AppProcess.APP_ID_ENV_VAR)

        self.assertEqual(marked.get(app_a.pid), "app-a")
        self.assertEqual(marked.get(app_b.pid), "app-b")

    def test_mid_session_reaps_only_untracked(self) -> None:
        """Mid-session: kill the marked process whose app id is untracked, spare the tracked one.

        Reproduces AppsManager._reap_untracked_orphans without needing the DB-backed manager:
        one process stands in for a still-tracked live app, the other for a stray.
        """
        tracked = self._spawn_sleeper(marker_value="tracked-app")
        stray = self._spawn_sleeper(marker_value="stray-app")

        marked, _denied = SysProc.find_marked_processes(AppProcess.APP_ID_ENV_VAR)
        tracked_ids = {"tracked-app"}  # stand-in for AppsManager.running_processes keys

        orphan_pids = [pid for pid, app_id in marked.items() if app_id not in tracked_ids]
        SysProc.killpg_of_pids(orphan_pids, reason="test untracked orphan")

        self.assertIn(stray.pid, orphan_pids)
        self.assertNotIn(tracked.pid, orphan_pids)
        self.assertTrue(_wait_gone(stray.pid), "untracked stray should be killed")
        self.assertFalse(_wait_gone(tracked.pid, timeout=1.0), "tracked app must survive")
