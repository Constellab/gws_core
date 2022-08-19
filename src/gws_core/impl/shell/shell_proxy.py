# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import subprocess
import time
from typing import Any, List

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import MessageObserver
from gws_core.core.utils.logger import Logger
from gws_core.impl.file.file_helper import FileHelper
from gws_core.task.task import Task


class ShellProxy():
    """
    Shell task proxy.

    This class is a proxy to Shell commandes. It allow running commands in a shell and get the output and stdout.
    """

    working_dir: str = None

    _message_dispatcher: MessageDispatcher = None

    def __init__(self, working_dir: str):
        super().__init__()
        self.working_dir = working_dir
        self._message_dispatcher = MessageDispatcher()

    def check_output(self, cmd: List[str], env: dict = None, text: bool = True,
                     shell_mode: bool = False) -> Any:

        try:
            output = subprocess.check_output(
                cmd,
                cwd=self.working_dir,
                text=text,
                env=env,
                shell=shell_mode
            )
            return output
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            raise Exception(f"The shell process has failed. Error {err}.")

    def run(self, cmd: List[str], env: dict = None,
            shell_mode: bool = False) -> None:

        FileHelper.create_dir_if_not_exist(self.working_dir)

        try:
            Logger.info(f"[ShellProxy] Running command: {cmd}")
            proc = subprocess.Popen(
                cmd,
                cwd=self.working_dir,
                env=env,
                shell=shell_mode,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            tic_a = time.perf_counter()
            stdout: list = []
            for line in iter(proc.stdout.readline, b''):
                stdout.append(line.decode().strip())
                tic_b = time.perf_counter()
                if tic_b - tic_a >= 0.1:      # save outputs every 0.1 sec in taskbar
                    self._message_dispatcher.notify_info_message("\n".join(stdout))
                    tic_a = time.perf_counter()
                    stdout = []
            if stdout:
                self._message_dispatcher.notify_info_message("\n".join(stdout))
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            self._message_dispatcher.notify_error_message(str(err))
            raise Exception(f"The shell process has failed. Error {err}.")

    def clean_working_dir(self):
        FileHelper.delete_dir(self.working_dir)

    def attach_task(self, task: Task) -> None:
        """Attach a task to the shell proxy. The logs of the proxy will be dispatch to the task logs

        :param task: _description_
        :type task: Task
        """
        self._message_dispatcher.attach_task(task)

    def attach_observer(self, observer: MessageObserver) -> None:
        """ Attach a custom observer to the shell proxy. The logs of the proxy will be dispatch to the observer"""
        self._message_dispatcher.attach(observer)
