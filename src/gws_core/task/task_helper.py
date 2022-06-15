# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Callable, Dict, Literal, Optional

from .task import Task


class NotifierMessage():
    status: Literal['SUCCESS', 'ERROR', 'WARNING', 'INFO', 'PROGRESS']
    message: str
    progress: Optional[float] = None

    def __init__(self, status: Literal['SUCCESS', 'ERROR', 'WARNING', 'INFO', 'PROGRESS'],
                 message: str,
                 progress: Optional[float] = None):
        self.status = status
        self.message = message
        self.progress = progress

    @staticmethod
    def create_success_message(message: str) -> 'NotifierMessage':
        return NotifierMessage(status='SUCCESS', message=message)

    @staticmethod
    def create_progress_message(progress: float, message: str) -> 'NotifierMessage':
        return NotifierMessage(status='PROGRESS', message=message, progress=progress)

    @staticmethod
    def create_error_message(message: str) -> 'NotifierMessage':
        return NotifierMessage(status='ERROR', message=message)

    @staticmethod
    def create_warning_message(message: str) -> 'NotifierMessage':
        return NotifierMessage(status='WARNING', message=message)

    @staticmethod
    def create_info_message(message: str) -> 'NotifierMessage':
        return NotifierMessage(status='INFO', message=message)


def notify_task(task: Task, message: NotifierMessage):
    """
    Notify a task of a from a NotifierMessage
    """
    if message.status == 'SUCCESS':
        task.log_success_message(message.message)
    elif message.status == 'ERROR':
        task.log_error_message(message.message)
    elif message.status == 'WARNING':
        task.log_warning_message(message.message)
    elif message.status == 'INFO':
        task.log_info_message(message.message)
    elif message.status == 'PROGRESS':
        task.update_progress_value(message.progress, message.message)


class MessageDispatcher:

    _observers: Dict[int, Callable[[NotifierMessage], None]] = None

    last_id: int = 0

    def __init__(self):
        self._observers = {}

    def attach(self, callback: Callable[[NotifierMessage], None]) -> int:
        """Attach the listener method and return an id to detach it later

        :param callback: method called when a message is sent
        :type callback: Callable[[NotifierMessage], None]
        :return: _description_
        :rtype: int
        """
        id = self.last_id
        self.last_id += 1
        self._observers[id] = callback
        return id

    def attach_task(self, task: Task) -> int:
        """
        Attach a task to update task messages when a message is sent.
        return an id to detach it later
        """

        if not isinstance(task, Task):
            Exception("Only a task can be attach to the task_helper")
        return self.attach(lambda message: notify_task(task, message))

    def detach(self, id: int) -> None:
        del self._observers[id]

    def notify_progress_value(self, progress: float, message: str) -> None:
        """
        Trigger an update in each subscriber.
        """
        self.notify_message(NotifierMessage.create_progress_message(progress, message))

    def notify_info_message(self, message: str) -> None:
        """
        Trigger an info in each subscriber.
        """
        self.notify_message(NotifierMessage.create_info_message(message))

    def notify_warning_message(self, message: str) -> None:
        """
        Trigger a warning in each subscriber.
        """
        self.notify_message(NotifierMessage.create_warning_message(message))

    def notify_error_message(self, message: str) -> None:
        """
        Trigger a error in each subscriber.
        """
        self.notify_message(NotifierMessage.create_error_message(message))

    def notify_success_message(self, message: str) -> None:
        """
        Trigger a success in each subscriber.
        """
        self.notify_message(NotifierMessage.create_success_message(message))

    def notify_message(self, message: NotifierMessage) -> None:
        """
        Trigger a message in each subscriber.
        """
        for observer in self._observers.values():
            observer(message)
