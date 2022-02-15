# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .task import Task


class TaskHelper:

    _observers: List[Task] = None

    def __init__(self):
        self._observers = []

    def attach(self, task: Task):
        if not isinstance(task, Task):
            BadRequestException("Only a task can be attache to the task_helper")
        self._observers.append(task)

    def detach(self, task: Task) -> None:
        self._observers.remove(task)

    def notify_progress_value(self, value: int, message: str) -> None:
        """
        Trigger an update in each subscriber.
        """

        for observer in self._observers:
            observer.update_progress_value(value, message)

    def notify_info_message(self, message: str) -> None:
        """
        Trigger an info in each subscriber.
        """
        for observer in self._observers:
            observer.log_info_message(message)

    def notify_warning_message(self, message: str) -> None:
        """
        Trigger a warning in each subscriber.
        """
        for observer in self._observers:
            observer.log_warning_message(message)

    def notify_error_message(self, message: str) -> None:
        """
        Trigger a error in each subscriber.
        """
        for observer in self._observers:
            observer.log_error_message(message)

    def notify_success_message(self, message: str) -> None:
        """
        Trigger a success in each subscriber.
        """
        for observer in self._observers:
            observer.log_success_message(message)
