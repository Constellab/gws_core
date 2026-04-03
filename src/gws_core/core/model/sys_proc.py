import contextlib
import os
import signal
import time

from psutil import Popen, Process

from ..exception.exceptions import BadRequestException


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
