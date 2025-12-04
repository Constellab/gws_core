import time
from threading import Timer
from typing import List, Optional

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

    # Prefix for all the messages
    prefix: str = None

    _observers: List[MessageObserver] = None

    # list of the messages that are waiting to be dispatched by the timer
    _waiting_messages: List[DispatchedMessage] = None

    # last time a message was notified
    _last_notify_time: float = None

    # store the timer to prevent to save the progress bar too often
    _waiting_dispatch_timer: Timer = None
    # store the thread when is it executing (after the timer and before it is finished)
    _running_dispatch_timers: List[Timer] = []

    # when set, the message dispatcher will forward the message to the parent dispatcher
    # after prefix and log level modification
    _parent_dispatcher: "MessageDispatcher" = None

    def __init__(
        self,
        interval_time_merging_message=0.1,
        interval_time_dispatched_buffer=1,
        log_level: MessageLevel = MessageLevel.INFO,
        prefix: str = None,
        parent_dispatcher: "MessageDispatcher" = None,
    ):
        self._observers = []
        self._waiting_messages = []
        self.interval_time_merging_message = interval_time_merging_message
        self.interval_time_dispatched_buffer = interval_time_dispatched_buffer
        self.message_level = log_level
        self.prefix = prefix
        self._parent_dispatcher = parent_dispatcher

    def attach(self, observer: MessageObserver) -> None:
        """Attach the listener method and return an id to detach it later

        :param callback: method called when a message is sent
        :type callback: Callable[[NotifierMessage], None]
        :return: _description_
        :rtype: int
        """
        if self.has_parent_dispatcher():
            raise Exception("Cannot attach an observer to a sub dispatcher")
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
        self._build_and_notify_message(message, MessageLevel.PROGRESS, progress)

    def notify_message_with_format(self, message: str) -> None:
        """
        Parse and trigger a message in each subscriber based on format prefix.

        Supported formats:
        - [INFO] Message - Sends an info message
        - [WARNING] Message - Sends a warning message
        - [ERROR] Message - Sends an error message
        - [SUCCESS] Message - Sends a success message
        - [DEBUG] Message - Sends a debug message
        - [PROGRESS:XX] Message - Sends a progress message with value XX (0-100)

        If no format prefix is found, the message is sent as an info message.

        Examples:
        - "[INFO] Processing data" -> Info message
        - "[WARNING] Low memory" -> Warning message
        - "[PROGRESS:50] Half way done" -> Progress at 50% with message "Half way done"
        - "[PROGRESS:75.5] Almost complete" -> Progress at 75.5%
        - "Regular message" -> Info message (no prefix)

        :param message: The formatted message string
        :type message: str
        """
        # Fast path: check for format prefix
        if not message.startswith("["):
            # No prefix, treat as info message
            self._build_and_notify_message(message, MessageLevel.INFO)
            return

        try:
            # Find the closing bracket
            close_idx = message.find("]")
            if close_idx == -1:
                # No closing bracket, treat as info message
                self._build_and_notify_message(message, MessageLevel.INFO)
                return

            # Extract the prefix (e.g., "INFO", "PROGRESS:50")
            prefix = message[1:close_idx]
            # Extract the message after the closing bracket (strip leading space)
            content = message[close_idx + 1 :].lstrip()

            # Check if it's a progress message with value
            if prefix.startswith("PROGRESS:"):
                value_str = prefix[9:]  # Remove "PROGRESS:" prefix
                progress_value = float(value_str)
                # Verify the progress value is between 0 and 100
                if 0 <= progress_value <= 100:
                    self._build_and_notify_message(content, MessageLevel.PROGRESS, progress_value)
                    return
                # Invalid progress value, treat as info message
                self._build_and_notify_message(message, MessageLevel.INFO)
                return

            # Map prefix to message level
            level_map = {
                "INFO": MessageLevel.INFO,
                "WARNING": MessageLevel.WARNING,
                "ERROR": MessageLevel.ERROR,
                "SUCCESS": MessageLevel.SUCCESS,
                "DEBUG": MessageLevel.DEBUG,
            }

            level = level_map.get(prefix)
            if level is not None:
                self._build_and_notify_message(content, level)
            else:
                # Unknown prefix, treat as info message with original content
                self._build_and_notify_message(message, MessageLevel.INFO)

        except (ValueError, IndexError):
            # If parsing fails, treat as normal info message
            self._build_and_notify_message(message, MessageLevel.INFO)

    def notify_info_message(self, message: str) -> None:
        """
        Trigger an info in each subscriber.
        """
        self._build_and_notify_message(message, MessageLevel.INFO)

    def notify_warning_message(self, message: str) -> None:
        """
        Trigger a warning in each subscriber.
        """
        self._build_and_notify_message(message, MessageLevel.WARNING)

    def notify_error_message(self, message: str) -> None:
        """
        Trigger a error in each subscriber.
        """
        self._build_and_notify_message(message, MessageLevel.ERROR)

    def notify_success_message(self, message: str) -> None:
        """
        Trigger a success in each subscriber.
        """
        self._build_and_notify_message(message, MessageLevel.SUCCESS)

    def notify_debug_message(self, message: str) -> None:
        """
        Trigger a debug in each subscriber.
        """
        self._build_and_notify_message(message, MessageLevel.DEBUG)

    def _build_and_notify_message(
        self, message: str, level: MessageLevel, progress: Optional[float] = None
    ) -> None:
        """
        Trigger a message in each subscriber.
        """
        if self.prefix is not None:
            message = f"{self.prefix} {message}"
        self.notify_message(DispatchedMessage(status=level, message=message, progress=progress))

    def notify_message(self, message: DispatchedMessage) -> None:
        """
        Trigger a message in each subscriber.
        """
        if not message.is_valid():
            return
        # if the message level is lower than the min level, we don't notify it
        if message.status.get_int_value() < self.message_level.get_int_value():
            return

        # if there is a parent dispatcher, we forward the message to it
        if self.has_parent_dispatcher():
            self._parent_dispatcher.notify_message(message)
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
            if (
                len(self._waiting_messages) > 0
                and self._waiting_messages[-1].status == message.status
            ):
                last_message = self._waiting_messages[-1]
                last_message.message += "\n" + message.message
                last_message.progress = message.progress
            # if there is no waiting message or the last message type is different, add the message
            else:
                self._waiting_messages.append(message)
        # add the message to the waiting list and launche a timer to dispatch the message
        else:
            self._waiting_messages.append(message)

        self._launch_dispatch_timer()
        self._last_notify_time = time.perf_counter()

    # launch a timer to dispatch the message after a delay
    def _launch_dispatch_timer(self):
        if self._waiting_dispatch_timer is None:
            self._waiting_dispatch_timer = Timer(
                self.interval_time_dispatched_buffer, self._dispatch_waiting_messages_after_timer
            )
            self._waiting_dispatch_timer.start()

    def _dispatch_waiting_messages_after_timer(self):
        #  set the waiting dispatch timer as the current dispatch timer
        current_dispatch_timer = self._waiting_dispatch_timer
        if current_dispatch_timer is not None:
            self._running_dispatch_timers.append(current_dispatch_timer)
        # clear the waiting dispatch timer
        self._waiting_dispatch_timer = None

        self._dispatch_waiting_messages()

        if current_dispatch_timer is not None:
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

    def has_parent_dispatcher(self) -> bool:
        return self._parent_dispatcher is not None

    def create_sub_dispatcher(
        self, log_level: Optional[MessageLevel] = None, prefix: Optional[str] = None
    ):
        """
        Create a sub dispatcher with the same configuration as the current dispatcher.
        The message will be forwarded to the parent dispatcher after prefix and log level modification.
        This is useful to override the prefix or the log level for a specific part of the code without
        affecting the parent dispatcher.
        """
        return MessageDispatcher(
            interval_time_merging_message=self.interval_time_merging_message,
            interval_time_dispatched_buffer=self.interval_time_dispatched_buffer,
            log_level=log_level or self.message_level,
            prefix=prefix or self.prefix,
            parent_dispatcher=self,
        )
