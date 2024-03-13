

import time
from threading import Timer
from typing import List

from gws_core.core.classes.observer.message_level import MessageLevel
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

    # Min level of message to be notified
    message_level: MessageLevel = None

    _observers: List[MessageObserver] = None

    # list of the messages that are waiting to be dispatched by the timer
    _waiting_messages: List[DispatchedMessage] = None

    # last time a message was notified
    _last_notify_time: float = None

    # store the timer to prevent to save the progress bar too often
    _waiting_dispatch_timer: Timer = None
    # store the thread when is it executing (after the timer and before it is finished)
    _running_dispatch_timers: List[Timer] = []

    def __init__(self, interval_time_merging_message=0.1, interval_time_dispatched_buffer=1,
                 log_level: MessageLevel = MessageLevel.INFO):
        self._observers = []
        self._waiting_messages = []
        self.interval_time_merging_message = interval_time_merging_message
        self.interval_time_dispatched_buffer = interval_time_dispatched_buffer
        self.message_level = log_level

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

    def notify_debug_message(self, message: str) -> None:
        """
        Trigger a debug in each subscriber.
        """
        self.notify_message(DispatchedMessage.create_debug_message(message))

    def notify_message(self, message: DispatchedMessage) -> None:
        """
        Trigger a message in each subscriber.
        """

        # if the message level is lower than the min level, we don't notify it
        if message.status.get_int_value() < self.message_level.get_int_value():
            return

        # if there is no dispatched time, then directly dispatch the message
        if self.interval_time_dispatched_buffer == 0:
            self._waiting_messages.append(message)
            self._dispatch_waiting_messages()
            return

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
        if self._waiting_dispatch_timer is None:
            self._waiting_dispatch_timer = Timer(self.interval_time_dispatched_buffer,
                                                 self._dispatch_waiting_messages_after_timer)
            self._waiting_dispatch_timer.start()

    def _dispatch_waiting_messages_after_timer(self):
        #  set the waiting dispatch timer as the current dispatch timer
        current_dispatch_timer = self._waiting_dispatch_timer
        if current_dispatch_timer is not None:
            self._running_dispatch_timers.append(current_dispatch_timer)
        # clear the waiting dispatch timer
        self._waiting_dispatch_timer = None

        self._dispatch_waiting_messages()

        # remove the running dispatch timer
        self._running_dispatch_timers.remove(current_dispatch_timer)

    def _dispatch_waiting_messages(self):
        # directly copy and clear the array because the observer update can take some times
        messages = self._waiting_messages.copy()
        self._waiting_messages.clear()
        if len(messages) > 0:
            for observer in self._observers:
                observer.update(messages)

    def force_dispatch_waiting_messages(self):
        # if there is a waiting dispatch timer, cancel it
        if self._waiting_dispatch_timer:
            self._waiting_dispatch_timer.cancel()
            self._waiting_dispatch_timer = None

        # wait for all the running dispatch timer to finish
        # because the dispatch_waiting_messages can take some times
        if len(self._running_dispatch_timers) > 0:
            for timer in self._running_dispatch_timers:
                timer.join()

        self._dispatch_waiting_messages()

    def has_observers(self):
        return len(self._observers) > 0
