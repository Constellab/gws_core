# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from threading import Timer
from typing import List

from gws_core.progress_bar.progress_bar import ProgressBar

from .dispatched_message import DispatchedMessage
from .message_observer import MessageObserver, ProgressBarMessageObserver


class MessageDispatcher:
    """Class to dispatch messages to observers. It has a built in
    buffer to merge messages and dispatch them in a single call to the observers.

    :return: _description_
    :rtype: _type_
    """

    # if the last message was send less than this time ago,
    # and the last message type is the same as the current one,
    # then the messages are merged separated by a new line
    interval_time_merging_message: float = None

    # During this time all the notify message are buffered before being dispatched all at once
    interval_time_dispatched_buffer: float = None

    _observers: List[MessageObserver] = None

    # list of the messages that are waiting to be dispatched by the timer
    _waiting_messages: List[DispatchedMessage] = None

    # last time a message was notified
    _last_notify_time: float = None

    # store the timer to prevent to save the progress bar too often
    _dispatch_timer: Timer = None

    def __init__(self, interval_time_merging_message=0.1, interval_time_dispatched_buffer=1):
        self._observers = []
        self._waiting_messages = []
        self.interval_time_merging_message = interval_time_merging_message
        self.interval_time_dispatched_buffer = interval_time_dispatched_buffer

    def attach(self, observer: MessageObserver) -> None:
        """Attach the listener method and return an id to detach it later

        :param callback: method called when a message is sent
        :type callback: Callable[[NotifierMessage], None]
        :return: _description_
        :rtype: int
        """
        self._observers.append(observer)

    def attach_progress_bar(self, progress_bar: ProgressBar) -> ProgressBarMessageObserver:
        """
        Attach a progress bar to update task messages when a message is sent.
        return an id to detach it later
        """

        if not isinstance(progress_bar, ProgressBar):
            Exception("Only a progress bar can be attached")
        observer = ProgressBarMessageObserver(progress_bar)
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

        if self._last_notify_time is None:
            self._last_notify_time = time.perf_counter()

        current_time = time.perf_counter()

        # time difference shorter than min_time_merge, we merge messages
        if current_time - self._last_notify_time < self.interval_time_merging_message:
            # if there is already a waiting message and the last message type is the same,
            # merge the messages
            if len(self._waiting_messages) > 0 and self._waiting_messages[-1].status == message.status:
                last_message = self._waiting_messages[-1]
                last_message.message += '\n' + message.message
                last_message.progress = message.progress
            # if there is no waiting message or the last message type is different, add the message
            else:
                self._waiting_messages.append(message)
        # add the message to the waiting list and launche a timer to dispatch the message
        else:
            self._waiting_messages.append(message)

        self._lauch_dispatch_timer()
        self._last_notify_time = time.perf_counter()

    # launche a timer to dispatch the message after a delay

    def _lauch_dispatch_timer(self):
        if self._dispatch_timer is None:
            self._dispatch_timer = Timer(self.interval_time_dispatched_buffer, self.dispatched_waiting_messages)
            self._dispatch_timer.start()

    def dispatched_waiting_messages(self):
        # if there is a timer, stop it and clean the variable
        if self._dispatch_timer:
            self._dispatch_timer.cancel()
            self._dispatch_timer = None

        # directly copy and clear the array because the observer update can take some times
        messages = self._waiting_messages.copy()
        self._waiting_messages.clear()
        if len(messages) > 0:
            for observer in self._observers:
                observer.update(messages)
