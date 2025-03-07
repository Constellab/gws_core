

from os import path
from unittest import TestCase

from gws_core import ShellProxy
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    BasicMessageObserver


# test_shell_proxy
class TestShellProxy(TestCase):

    def test_echo_in_file(self):
        with ShellProxy() as shell_proxy:

            result = shell_proxy.run(
                "echo \"John Doe\" > echo.txt", shell_mode=True)
            self.assertEqual(result, 0)

            # Check that the file was created with the content
            result_file_path = path.join(shell_proxy.working_dir, "echo.txt")
            with open(result_file_path, "r+t", encoding='utf-8') as fp:
                data = fp.read()
            self.assertEqual(data.strip(), "John Doe")

        # check that the working dir was deleted
        self.assertFalse(path.exists(shell_proxy.working_dir))

    def test_notified(self):
        # disable the time buffer for message so they are sent immediately
        dispatcher = MessageDispatcher(interval_time_dispatched_buffer=0)
        shell_proxy = ShellProxy(message_dispatcher=dispatcher)

        message_observer = BasicMessageObserver()
        shell_proxy.attach_observer(message_observer)

        result = shell_proxy.run('echo "AA" && ui', shell_mode=True, dispatch_stdout=True)
        self.assertNotEqual(result, 0)

        # Check that the message observer received echo AA info message
        self.assertEqual(len([
            x for x in message_observer.messages if x.message == "AA" and x.status == 'INFO']), 1)

        # Check that the message observer received ui error message
        error_message = [
            x for x in message_observer.messages if "ui: not found" in x.message and x.status == 'ERROR']
        self.assertEqual(len(error_message), 1)

        shell_proxy.clean_working_dir()

    def test_notified_2(self):
        """Test that multi lines echo are fully notified
        """
        # disable the time buffer for message so they are sent immediately
        dispatcher = MessageDispatcher(interval_time_dispatched_buffer=0)
        shell_proxy = ShellProxy(message_dispatcher=dispatcher)

        message_observer = BasicMessageObserver()
        shell_proxy.attach_observer(message_observer)

        result = shell_proxy.run('echo "AA\nBB"', shell_mode=True, dispatch_stdout=True)
        self.assertEqual(result, 0)

        # Check that the message observer received echo AA info message
        self.assertEqual(len([
            x for x in message_observer.messages if x.message == "AA" and x.status == 'INFO']), 1)
        self.assertEqual(len([
            x for x in message_observer.messages if x.message == "BB" and x.status == 'INFO']), 1)

        shell_proxy.clean_working_dir()

    def test_notified_error(self):

        # disable the time buffer for message so they are sent immediately
        dispatcher = MessageDispatcher(interval_time_dispatched_buffer=0)
        shell_proxy = ShellProxy(message_dispatcher=dispatcher)

        message_observer = BasicMessageObserver()
        shell_proxy.attach_observer(message_observer)

        result = shell_proxy.run('echo "AA" && ui', shell_mode=True,
                                 dispatch_stdout=False, dispatch_stderr=True)
        self.assertNotEqual(result, 0)

        # Check that the message observer received echo AA info message
        self.assertEqual(len([
            x for x in message_observer.messages if x.message == "AA" and x.status == 'INFO']), 0)
        self.assertEqual(len([
            x for x in message_observer.messages if "ui: not found" in x.message and x.status == 'ERROR']), 1)

        shell_proxy.clean_working_dir()
