# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from os import path
from unittest import IsolatedAsyncioTestCase

from gws_core import ShellProxy
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    BasicMessageObserver


# test_shell_proxy
class TestShellProxy(IsolatedAsyncioTestCase):

    def test_echo_in_file(self):
        shell_proxy = ShellProxy()

        result = shell_proxy.run([f"echo \"John Doe\" > echo.txt"], shell_mode=True)
        self.assertEqual(result, 0)

        # Check that the file was created with the content
        result_file_path = path.join(shell_proxy.working_dir, "echo.txt")
        with open(result_file_path, "r+t") as fp:
            data = fp.read()
        self.assertEqual(data.strip(), "John Doe")

        shell_proxy.clean_working_dir()

    def test_notified(self):
        # disable the time buffer for message so they are sent immediately
        dispatcher = MessageDispatcher(interval_time_dispatched_buffer=0)
        shell_proxy = ShellProxy(message_dispatcher=dispatcher)

        message_observer = BasicMessageObserver()
        shell_proxy.attach_observer(message_observer)

        result = shell_proxy.run([f'echo "AA" && ui'], shell_mode=True)
        self.assertNotEqual(result, 0)

        # Check that the message observer received echo AA info message
        echo_message = [x for x in message_observer.messages if x.message == "AA" and x.status == 'INFO']
        self.assertEqual(len(echo_message), 1)

        # Check that the message observer received ui error message
        error_message = [x for x in message_observer.messages if "ui: not found" in x.message and x.status == 'ERROR']
        self.assertEqual(len(error_message), 1)

        shell_proxy.clean_working_dir()
