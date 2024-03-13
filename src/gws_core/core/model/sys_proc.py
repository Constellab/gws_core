

from typing import List

from psutil import Popen, Process

from ..exception.exceptions import BadRequestException

# ####################################################################
#
# SysProc
#
# ####################################################################


class SysProc:
    """
    SysProc class.

    Wrapper of `psutil.Process` class.
    This class that only exposes necessary functionalities to easily manage shell processes.
    """

    _process: Process = None

    @staticmethod
    def from_pid(pid) -> 'SysProc':
        proc = SysProc()
        proc._process = Process(pid)
        return proc

    def is_alive(self) -> bool:
        return self._process.is_running()

    def is_zombie(self) -> bool:
        return self._process.status() == "zombie"

    def kill(self):
        self._process.kill()

    def kill_with_children(self):
        for child in self.get_all_children():
            child.kill()
        self.kill()

    def get_all_children(self) -> List[Process]:
        """Return all the chlidren of process recursively.

        :return: _description_
        :rtype: List[Process]
        """
        return self._process.children(recursive=True)

    @property
    def pid(self) -> int:
        if self._process is None:
            return 0
        return self._process.pid

    @classmethod
    def popen(cls, cmd, *args, **kwargs) -> 'SysProc':
        try:
            proc = SysProc()
            proc._process = Popen(cmd, *args, **kwargs)
            return proc
        except Exception as err:
            raise BadRequestException(
                f"An error occured when calling command {cmd}. Error: {err}") from err

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
