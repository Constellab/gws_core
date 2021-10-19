
import psutil

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

    _ps: psutil.Process = None

    @staticmethod
    def from_pid(pid) -> 'SysProc':
        proc = SysProc()
        proc._ps = psutil.Process(pid)
        return proc

    def is_alive(self) -> bool:
        return self._ps.is_running()

    def kill(self):
        self._ps.kill()

    @property
    def pid(self) -> int:
        if self._ps is None:
            return 0
        return self._ps.pid

    @classmethod
    def popen(cls, cmd, *args, **kwargs) -> 'SysProc':
        try:
            proc = SysProc()
            proc._ps = psutil.Popen(cmd, *args, **kwargs)
            return proc
        except Exception as err:
            raise BadRequestException(
                f"An error occured when calling command {cmd}. Error: {err}") from err

    def stats(self) -> dict:
        """
        Get process statistics
        """
        return self._ps.as_dict()

    @property
    def stdout(self):
        if isinstance(self._ps, psutil.Popen):
            return self._ps.stdout
        return None

    @property
    def stderr(self):
        if isinstance(self._ps, psutil.Popen):
            return self._ps.stderr
        return None

    def wait(self, timeout=None):
        """
        Wait for a process PID to terminate
        """
        self._ps.wait(timeout=timeout)
