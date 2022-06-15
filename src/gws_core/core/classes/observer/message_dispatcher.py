# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from asyncio import Task
from typing import List

from .dispatched_message import DispatchedMessage
from .message_observer import MessageObserver, TaskProgressMessageObserver


class MessageDispatcher:

    _observers: List[MessageObserver] = None

    def __init__(self):
        self._observers = []

    def attach(self, observer: MessageObserver) -> None:
        """Attach the listener method and return an id to detach it later

        :param callback: method called when a message is sent
        :type callback: Callable[[NotifierMessage], None]
        :return: _description_
        :rtype: int
        """
        self._observers.append(observer)

    def attach_task(self, task: Task) -> TaskProgressMessageObserver:
        """
        Attach a task to update task messages when a message is sent.
        return an id to detach it later
        """

        if not isinstance(task, Task):
            Exception("Only a task can be attach to the task_helper")
        observer = TaskProgressMessageObserver(task)
        self.attach(observer)
        return observer

    def detach(self, observer: MessageObserver) -> None:
        self._observers.remove(observer)

    def notify_progress_value(self, progress: float, message: str) -> None:
        """
        Trigger an update in each subscriber.
        """
        self.notify_message(DispatchedMessage.create_progress_message(progress, message))

    def notify_info_message(self, message: str) -> None:
        """
        Trigger an info in each subscriber.
        """
        self.notify_message(DispatchedMessage.create_info_message(message))

    def notify_warning_message(self, message: str) -> None:
        """
        Trigger a warning in each subscriber.
        """
        self.notify_message(DispatchedMessage.create_warning_message(message))

    def notify_error_message(self, message: str) -> None:
        """
        Trigger a error in each subscriber.
        """
        self.notify_message(DispatchedMessage.create_error_message(message))

    def notify_success_message(self, message: str) -> None:
        """
        Trigger a success in each subscriber.
        """
        self.notify_message(DispatchedMessage.create_success_message(message))

    def notify_message(self, message: DispatchedMessage) -> None:
        """
        Trigger a message in each subscriber.
        """
        for observer in self._observers:
            observer.update(message)
