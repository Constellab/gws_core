# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import List

from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.progress_bar.progress_bar import (ProgressBar,
                                                ProgressBarMessageWithType)

from .dispatched_message import DispatchedMessage


class MessageObserver:

    @abstractmethod
    def update(self, messages: List[DispatchedMessage]) -> None:
        """Method called when a message is dispatched"""


class ProgressBarMessageObserver(MessageObserver):
    """Observer to log dispatched message to a progress bar

    :param MessageObserver: _description_
    :type MessageObserver: _type_
    """

    progress_bar: ProgressBar

    def __init__(self, progress_bar: ProgressBar):
        super().__init__()
        self.progress_bar = progress_bar

    def update(self, messages: List[DispatchedMessage]) -> None:

        # convert message to ProgressBarMessageWithType
        progress_bar_messages: List[ProgressBarMessageWithType] = [
            {'message': message.message, 'type': message.status,
                'progress': message.progress}
            for message in messages
        ]

        self.progress_bar.add_messages(progress_bar_messages)


class BasicMessageObserver(MessageObserver):

    messages: List[DispatchedMessage]

    def __init__(self) -> None:
        super().__init__()
        self.messages = []

    def update(self, messages: List[DispatchedMessage]) -> None:
        self.messages.extend(messages)

    def has_message_containing(self, sub_text: str, level: MessageLevel = None) -> bool:
        for message in self.messages:
            if level is not None and message.status != level:
                continue
            if sub_text in message.message:
                return True
        return False
