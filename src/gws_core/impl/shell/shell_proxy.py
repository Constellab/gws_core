

import select
import subprocess
from threading import Thread
from typing import Any, List, Union

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import MessageObserver
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.utils.logger import Logger
from gws_core.impl.file.file_helper import FileHelper
from gws_core.progress_bar.progress_bar import ProgressBar

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...core.utils.settings import Settings


class ShellProxy():
    """
    Shell task proxy.

    This class is a proxy to Shell commandes. It allow running commands in a shell and get the output and stdout.
    """

    working_dir: str = None

    _message_dispatcher: MessageDispatcher = None

    def __init__(self, working_dir: str = None, message_dispatcher: MessageDispatcher = None):
        """_summary_

        :param working_dir: working directory for the shell (all command will be executed from this dir).
                            If not provided, an new temp directory is created. defaults to None
        :type working_dir: str, optional
        :param message_dispatcher: if provided, the output of the command will be redirected to the dispatcher.
                                  Can be useful to log command outputs in task's logs. defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        """
        super().__init__()

        if working_dir is not None:
            self.working_dir = working_dir
        else:
            self.working_dir = Settings.get_instance().make_temp_dir()

        if message_dispatcher is not None:
            self._message_dispatcher = message_dispatcher
        else:
            self._message_dispatcher = MessageDispatcher()

    def run(self, cmd: Union[list, str], env: dict = None,
            shell_mode: bool = False) -> int:
        """
        Run a command in a shell.
        The logs of the command will be dispatched to the message dispatcher during the execution.

        :param cmd: command to run
        :type cmd: Union[list, str]
        :param env: environment variables to pass to the shell, defaults to None
        :type env: dict, optional
        :param shell_mode: if True, the command is run in a shell, defaults to False
        :type shell_mode: bool, optional
        """
        self._check_before_run(cmd, env, shell_mode)

        FileHelper.create_dir_if_not_exist(self.working_dir)

        self._message_dispatcher.notify_info_message(
            f"[ShellProxy] Running command: {cmd}")
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.working_dir,
                env=env,
                shell=shell_mode,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self._message_dispatcher.notify_info_message(
                f"[ShellProxy] Running command in process : {proc.pid}")

            # use to read the stdout and stderr of the process
            # https://stackoverflow.com/questions/12270645/can-you-make-a-python-subprocess-output-stdout-and-stderr-as-usual-but-also-cap/12272262#12272262
            while True:
                # get the file descriptors of the stdout and stderr
                reads = [proc.stdout.fileno(), proc.stderr.fileno()]

                # return the list of file descriptors that are ready to be read
                ret = select.select(reads, [], [])

                has_read: bool = False

                for file_no in ret[0]:
                    # read the stdout
                    if file_no == proc.stdout.fileno():
                        read = proc.stdout.readline()
                        if read:
                            self._self_dispatch_stdout(read)
                            has_read = True

                    # read the stderr
                    if file_no == proc.stderr.fileno():
                        read = proc.stderr.readline()
                        if read:
                            self._self_dispatch_stderr(read)
                            has_read = True

                poll = proc.poll()

                # stop if the process has finished and there is no more data to read
                # we need to check if there is no more data to read because the process can be finished but there is still data in the buffer (if long log at the end)
                if poll is not None and not has_read:
                    break

            # wait for the process to finish, use comminicate to avoir deadlock if messages are still in the buffer
            # The communicate should always return empty output.
            outs, errs = proc.communicate()
            if outs:
                self._message_dispatcher.notify_error_message(
                    "[ShellProxy] The communicate method has returned an stdout output. This is not expected.")
                self._self_dispatch_stdout(outs)
            if errs:
                self._message_dispatcher.notify_error_message(
                    "[ShellProxy] The communicate method has returned an stderr output. This is not expected.")
                self._self_dispatch_stderr(errs)

            # retrieve the return code of the process and dispatch the message to the observers
            # we can use wait instead of poll because we have already called communicate
            return_core = proc.poll()
            if return_core == 0:
                self._message_dispatcher.notify_info_message(
                    "[ShellProxy] Command executed successfully")
            else:
                self._message_dispatcher.notify_error_message(
                    "[ShellProxy] Command failed")

            self.dispatch_waiting_messages()

            return return_core
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            self._message_dispatcher.notify_error_message(str(err))
            raise Exception(f"The shell process has failed. Error {err}.")

    def run_in_new_thread(self, cmd: Union[list, str], env: dict = None,
                          shell_mode: bool = False) -> SysProc:
        """
        Run a command in a shell without blocking the thread.
        The logs of the command will be dispatched to the message dispatcher during the execution.

        :param cmd: command to run
        :type cmd: Union[list, str]
        :param env: environment variables to pass to the shell, defaults to None
        :type env: dict, optional
        :param shell_mode: if True, the command is run in a shell, defaults to False
        :type shell_mode: bool, optional
        :return: Thread running the command
        :rtype: threading.Thread
        """
        self._check_before_run(cmd, env, shell_mode)

        FileHelper.create_dir_if_not_exist(self.working_dir)

        self._message_dispatcher.notify_info_message(
            f"[ShellProxy] Running command: {cmd}")

        return SysProc.popen(cmd, cwd=self.working_dir, env=env, shell=shell_mode)

    def check_output(self, cmd: Union[list, str], env: dict = None,
                     shell_mode: bool = False, text: bool = True) -> Any:
        """
        Run a command in a shell and return the output.

        :param cmd: command to run
        :type cmd: Union[list, str]
        :param env: environment variables to pass to the shell, defaults to None
        :type env: dict, optional
        :param shell_mode: if True, the command is run in a shell, defaults to False
        :type shell_mode: bool, optional
        :param text: if True, the output is returned as a string, defaults to True
        :type text: bool, optional
        :raises Exception: _description_
        :return: output of the command
        :rtype: Any
        """
        self._check_before_run(cmd, env, shell_mode)

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

    def _check_before_run(self, cmd: Union[list, str], env: dict = None,
                          shell_mode: bool = False) -> None:
        """Check if the command can be run before running it.
        """
        if env is not None and not isinstance(env, dict):
            raise ValueError(
                "'env' must return a dictionnary")

        if shell_mode:
            if isinstance(cmd, list):
                raise ValueError(
                    "The command must be a string and not a list if the shell mode is activated")
        else:
            if not isinstance(cmd, list):
                raise ValueError(
                    "The command must be a list and not a string if the shell mode is not activated")

    def _self_dispatch_stdouts(self, messages: List[bytes]) -> None:
        if len(messages) > 0:
            message = "\n".join([message.decode().strip()
                                for message in messages])
            self._message_dispatcher.notify_info_message(message)

    def _self_dispatch_stderrs(self, messages: List[bytes]) -> None:
        if len(messages) > 0:
            message = "\n".join([message.decode().strip()
                                for message in messages])
            self._message_dispatcher.notify_error_message(message)

    def _self_dispatch_stdout(self, message: bytes) -> None:
        self._message_dispatcher.notify_info_message(
            message.decode().strip())

    def _self_dispatch_stderr(self, message: bytes) -> None:
        self._message_dispatcher.notify_error_message(
            message.decode().strip())

    def clean_working_dir(self):
        FileHelper.delete_dir(self.working_dir)

    def attach_progress_bar(self, progress_bar: ProgressBar) -> None:
        """Attach a progress_bar to the shell proxy. The logs of the proxy will be dispatch to the progress_bar logs
        """
        self._message_dispatcher.attach_progress_bar(progress_bar)

    def attach_observer(self, observer: MessageObserver) -> None:
        """ Attach a custom observer to the shell proxy. The logs of the proxy will be dispatch to the observer"""
        self._message_dispatcher.attach(observer)

    def dispatch_waiting_messages(self) -> None:
        self._message_dispatcher.force_dispatch_waiting_messages()

    def get_message_dispatcher(self) -> MessageDispatcher:
        """ Get the message dispatcher """
        return self._message_dispatcher

    def log_info_message(self, message: str):
        """ Log an info message using the dispatcher """
        self._message_dispatcher.notify_info_message(message)

    def log_error_message(self, message: str):
        """ Log an error message using the dispatcher """
        self._message_dispatcher.notify_error_message(message)

    def log_warning_message(self, message: str):
        """ Log a warining message using the dispatcher """
        self._message_dispatcher.notify_warning_message(message)

    def __enter__(self):
        # add support for with statement
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # add support for with statement
        self.clean_working_dir()
        return True
