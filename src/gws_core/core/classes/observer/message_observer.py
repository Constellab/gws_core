# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import List

from gws_core.task.task import Task

from .dispatched_message import DispatchedMessage


class MessageObserver:

    @abstractmethod
    def update(self, message: DispatchedMessage) -> None:
        """Method called when a message is dispatched"""


class TaskProgressMessageObserver(MessageObserver):
    """Observer to log dispatched message to a task progress bar

    :param MessageObserver: _description_
    :type MessageObserver: _type_
    """

    task: Task

    def __init__(self, task: Task):
        super().__init__()
        self.task = task

    def update(self, message: DispatchedMessage) -> None:
        if message.status == 'SUCCESS':
            self.task.log_success_message(message.message)
        elif message.status == 'ERROR':
            self.task.log_error_message(message.message)
        elif message.status == 'WARNING':
            self.task.log_warning_message(message.message)
        elif message.status == 'INFO':
            self.task.log_info_message(message.message)
        elif message.status == 'PROGRESS':
            self.task.update_progress_value(message.progress, message.message)


class BasicMessageObserver(MessageObserver):

    messages: List[DispatchedMessage]

    def __init__(self) -> None:
        super().__init__()
        self.messages = []

    def update(self, message: DispatchedMessage) -> None:
        self.messages.append(message)
