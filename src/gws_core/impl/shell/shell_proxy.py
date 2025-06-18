import os
import select
import subprocess
from enum import Enum
from typing import IO, Any, Callable, List, Optional, Union

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import MessageObserver
from gws_core.core.model.base_typing import BaseTyping
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.model.typing_register_decorator import typing_registrator
from gws_core.progress_bar.progress_bar import ProgressBar


class ShellProxyDTO(BaseModelDTO):
    typing_name: str
    env_code: Optional[str] = None


class ShellIO():
    io: IO
    dispatch: Callable

    def __init__(self, io: IO, dispatch: Callable) -> None:
        self.io = io
        self.dispatch = dispatch


class ShellProxyEnvVariableMode(Enum):
    """
    Enum for the shell proxy environmentvariable mode.
    """
    MERGE = "merge"  # merge the provided environment variables with the current environment
    REPLACE = "replace"  # replace the current environment with the provided environment variables


@typing_registrator(unique_name="ShellProxy", object_type="MODEL", hide=True)
class ShellProxy(BaseTyping):
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
                                    In a task it can be used provided like this : ShellProxy(message_dispatcher=self.message_dispatcher)
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

    def run(self, cmd: Union[list, str],
            env: dict = None,
            env_mode: ShellProxyEnvVariableMode = ShellProxyEnvVariableMode.MERGE,
            shell_mode: bool = False,
            dispatch_stdout: bool = False,
            dispatch_stderr: bool = True) -> int:
        """
        Run a command in a shell.
        The logs of the command will be dispatched to the message dispatcher during the execution.

        :param cmd: command to run
        :type cmd: Union[list, str]
        :param env: environment variables to pass to the shell, defaults to None
        :type env: dict, optional
        :param env_mode: mode to use for the environment variables, defaults to ShellProxyEnvVariableMode.MERGE
        :type env_mode: ShellProxyEnvVariableMode, optional
        :param shell_mode: if True, the command is run in a shell, defaults to False
        :type shell_mode: bool, optional
        :param dispatch_stdout: if True, the stdout of the command is dispatched to the message dispatcher.
                            ⚠️ Warning ⚠️ Do not set to True if the command generates a lot of logs,
                            because logs are stored in database, defaults to False
        :type dispatch_stdout: bool, optional
        :param dispatch_stderr: if True, the stderr of the command is dispatched to the message dispatcher.
                            ⚠️ Warning ⚠️ Do not set to True if the command generates a lot of logs,
                            because logs are stored in database, defaults to True
        :type dispatch_stderr: bool, optional
        """
        self._check_before_run(cmd, shell_mode)

        env = self._prepare_env(env, env_mode)

        FileHelper.create_dir_if_not_exist(self.working_dir)

        self._message_dispatcher.notify_info_message(
            f"[ShellProxy] Running command: {cmd}")
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.working_dir,
                env=env,
                shell=shell_mode,
                stdout=subprocess.PIPE if dispatch_stdout else subprocess.DEVNULL,
                stderr=subprocess.PIPE if dispatch_stderr else subprocess.DEVNULL
            )

            self._message_dispatcher.notify_info_message(
                f"[ShellProxy] Running command in process : {proc.pid}")

            # get the file descriptors of the stdout and stderr
            shell_io: List[ShellIO] = []
            if dispatch_stdout:
                shell_io.append(ShellIO(io=proc.stdout, dispatch=self._self_dispatch_stdout))

            if dispatch_stderr:
                shell_io.append(ShellIO(io=proc.stderr, dispatch=self._self_dispatch_stderr))

            if len(shell_io) > 0:
                self._manage_run_output(proc, shell_io)

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

    def _manage_run_output(self, proc: subprocess.Popen, loggers: List[ShellIO]) -> None:
        # use to read the stdout and stderr of the process
        # https://stackoverflow.com/questions/12270645/can-you-make-a-python-subprocess-output-stdout-and-stderr-as-usual-but-also-cap/12272262#12272262
        reads = [logger.io.fileno() for logger in loggers]

        while True:
            # return the list of file descriptors that are ready to be read
            ret = select.select(reads, [], [])

            has_read: bool = False

            for file_no in ret[0]:

                # log stdout or stderr
                for logger in loggers:
                    if file_no == logger.io.fileno():
                        read = logger.io.readline()
                        if read:
                            logger.dispatch(read)
                            has_read = True

            poll = proc.poll()

            # stop if the process has finished and there is no more data to read
            # we need to check if there is no more data to read because the process can be finished but there is still data in the buffer (if long log at the end)
            if poll is not None and not has_read:
                break

    def run_in_new_thread(self, cmd: Union[list, str],
                          env: dict = None,
                          env_mode: ShellProxyEnvVariableMode = ShellProxyEnvVariableMode.MERGE,
                          shell_mode: bool = False,
                          ) -> SysProc:
        """
        Run a command in a shell without blocking the thread.
        The logs of the command are ignored.

        :param cmd: command to run
        :type cmd: Union[list, str]
        :param env: environment variables to pass to the shell, defaults to None
        :type env: dict, optional
        :param env_mode: mode to use for the environment variables, defaults to ShellProxyEnvVariableMode.MERGE
        :type env_mode: ShellProxyEnvVariableMode, optional
        :param shell_mode: if True, the command is run in a shell, defaults to False
        :type shell_mode: bool, optional
        :return: Thread running the command
        :rtype: threading.Thread
        """
        self._check_before_run(cmd, shell_mode)

        env = self._prepare_env(env, env_mode)

        FileHelper.create_dir_if_not_exist(self.working_dir)

        self._message_dispatcher.notify_info_message(
            f"[ShellProxy] Running command: {cmd}")

        return SysProc.popen(cmd, cwd=self.working_dir, env=env, shell=shell_mode)

    def check_output(self, cmd: Union[list, str],
                     env: dict = None,
                     env_mode: ShellProxyEnvVariableMode = ShellProxyEnvVariableMode.MERGE,
                     shell_mode: bool = False, text: bool = True) -> Any:
        """
        Run a command in a shell and return the output.
        The logs of the command are ignored.

        :param cmd: command to run
        :type cmd: Union[list, str]
        :param env: environment variables to pass to the shell, defaults to None
        :type env: dict, optional
        :param shell_mode: if True, the command is run in a shell, defaults to False
        :type shell_mode: bool, optional
        :param env_mode: mode to use for the environment variables, defaults to ShellProxyEnvVariableMode.MERGE
        :type env_mode: ShellProxyEnvVariableMode, optional
        :param text: if True, the output is returned as a string, defaults to True
        :type text: bool, optional
        :raises Exception: _description_
        :return: output of the command
        :rtype: Any
        """
        self._check_before_run(cmd, shell_mode)

        env = self._prepare_env(env, env_mode)

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

    def _check_before_run(self, cmd: Union[list, str],
                          shell_mode: bool = False) -> None:
        """Check if the command can be run before running it.
        """
        if shell_mode:
            if isinstance(cmd, list):
                raise ValueError(
                    "The command must be a string and not a list if the shell mode is activated")
        else:
            if not isinstance(cmd, list):
                raise ValueError(
                    "The command must be a list and not a string if the shell mode is not activated")

    def _prepare_env(self, env: dict, mode: ShellProxyEnvVariableMode) -> dict | None:
        """Prepare the environment variables to be used in the shell command.
        If the mode is MERGE, the provided environment variables are merged with the current environment.
        If the mode is REPLACE, the provided environment variables replace the current environment.

        :param env: environment variables to prepare
        :type env: dict
        :param mode: mode to use for preparing the environment variables
        :type mode: ShellProxyEnvVariableMode
        :return: prepared environment variables
        :rtype: dict
        """
        if env is None:
            return None

        if env is not None and not isinstance(env, dict):
            raise ValueError(
                "'env' must return a dictionnary")

        if mode == ShellProxyEnvVariableMode.REPLACE:
            return env
        else:
            merged_env = os.environ.copy()
            merged_env.update(env)
            return merged_env

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

    def to_dto(self) -> ShellProxyDTO:
        return ShellProxyDTO(
            typing_name=self.get_typing_name(),
        )
