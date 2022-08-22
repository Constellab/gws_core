# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import selectors
import subprocess
import time
from typing import Any, List, Literal, Union

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import MessageObserver
from gws_core.core.utils.logger import Logger
from gws_core.impl.file.file_helper import FileHelper
from gws_core.task.task import Task

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...core.utils.settings import Settings


class ShellProxy():
    """
    Shell task proxy.

    This class is a proxy to Shell commandes. It allow running commands in a shell and get the output and stdout.
    """

    # When running a command, the messages are buffered and dispatched every 1 seconds
    _NOTIFY_MESSAGE_INTERVAL = 1

    working_dir: str = None

    _message_dispatcher: MessageDispatcher = None

    def __init__(self, working_dir: str = None):
        """_summary_

        :param working_dir: working directory for the shell (all command will be executed from this dir)
                            if not provided, an new temp directory is created, defaults to None
        :type working_dir: str, optional
        """
        super().__init__()

        if working_dir is not None:
            self.working_dir = working_dir
        else:
            self.working_dir = Settings.retrieve().make_temp_dir()
        self._message_dispatcher = MessageDispatcher()

    def check_output(self, cmd: Union[list, str], env: dict = None, text: bool = True,
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

    def run(self, cmd: Union[list, str], env: dict = None,
            shell_mode: bool = False) -> int:

        if env is not None and not isinstance(env, dict):
            raise BadRequestException(
                "Method 'build_os_env' must return a dictionnary")

        FileHelper.create_dir_if_not_exist(self.working_dir)

        self._message_dispatcher.notify_info_message(f"[ShellProxy] Running command: {cmd}")
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.working_dir,
                env=env,
                shell=shell_mode,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # use to read the stdout and stderr of the process
            sel = selectors.DefaultSelector()
            sel.register(proc.stdout, selectors.EVENT_READ)
            sel.register(proc.stderr, selectors.EVENT_READ)

            process_ended = False

            while not process_ended:
                for key, _ in sel.select():
                    data: str = key.fileobj.read1().decode().strip()

                    # when the process has finished
                    if not data:
                        process_ended = True
                        break

                    # dispatch the message to the observers
                    if key.fileobj is proc.stdout:
                        self._message_dispatcher.notify_info_message(data)
                    else:
                        self._message_dispatcher.notify_error_message(data)

            # retrieve the return code of the process and dispatch the message to the observers
            return_core = proc.wait()
            if return_core == 0:
                self._message_dispatcher.notify_info_message("[ShellProxy] Command executed successfully")
            else:
                self._message_dispatcher.notify_error_message("[ShellProxy] Command failed")

            return return_core
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
