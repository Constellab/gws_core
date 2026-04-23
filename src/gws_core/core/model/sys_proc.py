import contextlib
import os
import signal
import time

import psutil
from psutil import Popen, Process

from ..exception.exceptions import BadRequestException
from ..utils.logger import Logger


class SysProc:
    """
    SysProc class.

    Wrapper of `psutil.Process` class.
    This class that only exposes necessary functionalities to easily manage shell processes.
    """

    _process: Process | None = None
    _use_process_group: bool = False

    def __init__(self, process: Process | None = None, use_process_group: bool = False):
        self._process = process
        self._use_process_group = use_process_group

    def get_process(self) -> Process:
        return self._process

    def is_alive(self) -> bool:
        return self._process.is_running()

    def is_zombie(self) -> bool:
        return self._process.status() == "zombie"

    def kill(self):
        self._process.kill()

    def kill_with_children(self):
        """Kill the process and all its children.

        If the process was started with a process group (start_new_session=True),
        sends SIGTERM to the entire process group first for graceful shutdown,
        waits briefly, then sends SIGKILL to any survivors.
        Otherwise, falls back to killing each child individually.
        """
        if self._use_process_group:
            self._kill_process_group()
        else:
            for child in self.get_all_children():
                child.kill()
            self.kill()

    def _kill_process_group(self):
        """Kill the entire process group: SIGTERM first, then SIGKILL after a short wait."""
        try:
            pgid = os.getpgid(self._process.pid)
        except (ProcessLookupError, OSError):
            # Process already gone
            return

        # Send SIGTERM to the entire process group for graceful shutdown
        try:
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            return

        # Wait up to 5 seconds for processes to terminate gracefully
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if not self._process.is_running():
                return
            time.sleep(0.2)

        # Force kill any survivors
        with contextlib.suppress(ProcessLookupError, OSError):
            os.killpg(pgid, signal.SIGKILL)

    def get_all_children(self) -> list[Process]:
        """Return all the chlidren of process recursively.

        :return: _description_
        :rtype: List[Process]
        """
        return self._process.children(recursive=True)

    def stats(self) -> dict:
        """
        Get process statistics
        """
        return self._process.as_dict()

    def wait(self, timeout=None):
        """
        Wait for a process PID to terminate
        """
        self._process.wait(timeout=timeout)

    @property
    def pid(self) -> int:
        if self._process is None:
            return 0
        return self._process.pid

    @classmethod
    def popen(cls, cmd, *args, **kwargs) -> "SysProc":
        try:
            use_process_group = kwargs.get("start_new_session", False)
            return SysProc(Popen(cmd, *args, **kwargs), use_process_group=use_process_group)
        except Exception as err:
            raise BadRequestException(
                f"An error occured when calling command {cmd}. Error: {err}"
            ) from err

    @staticmethod
    def from_pid(pid) -> "SysProc":
        return SysProc(Process(pid))

    @staticmethod
    def kill_process_on_port(port: int) -> list[int]:
        """Find any process with a LISTEN socket on `port` and kill it (and its children).

        Returns the list of PIDs that were targeted (may be empty).
        Logs a warning per offender before killing so the event is traceable
        without relying on the caller to log.

        If the OS denies access to enumerate sockets (e.g. non-root on some systems),
        logs a warning and returns an empty list — the subprocess will then fail
        to bind on its own as before.
        """
        try:
            connections = psutil.net_connections(kind="inet")
        except psutil.AccessDenied:
            Logger.warning(
                "Cannot enumerate listening sockets (permission denied) — skipping port pre-clean"
            )
            return []

        offender_pids: list[int] = []
        for conn in connections:
            if (
                conn.status == psutil.CONN_LISTEN
                and conn.laddr
                and conn.laddr.port == port
                and conn.pid is not None
                and conn.pid not in offender_pids
            ):
                offender_pids.append(conn.pid)

        killed_pids: list[int] = []
        for pid in offender_pids:
            with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                proc = Process(pid)
                try:
                    proc_name = proc.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc_name = "<unknown>"
                try:
                    proc_cmdline = proc.cmdline()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc_cmdline = []

                Logger.warning(
                    f"Port {port} is held by orphan process pid={pid} name={proc_name} "
                    f"cmdline={proc_cmdline!r} — killing it"
                )

                SysProc(proc).kill_with_children()
                killed_pids.append(pid)
                Logger.info(f"Freed port {port} (killed pid={pid})")

        return killed_pids
