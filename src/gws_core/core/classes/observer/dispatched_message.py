
from .message_level import MessageLevel


class DispatchedMessage:
    status: MessageLevel
    message: str
    progress: float | None = None

    def __init__(self, status: MessageLevel, message: str, progress: float | None = None):
        self.status = status
        self.message = message
        self.progress = progress

    @staticmethod
    def create_success_message(message: str) -> "DispatchedMessage":
        return DispatchedMessage(status=MessageLevel.SUCCESS, message=message)

    @staticmethod
    def create_progress_message(progress: float, message: str) -> "DispatchedMessage":
        return DispatchedMessage(status=MessageLevel.PROGRESS, message=message, progress=progress)

    @staticmethod
    def create_error_message(message: str) -> "DispatchedMessage":
        return DispatchedMessage(status=MessageLevel.ERROR, message=message)

    @staticmethod
    def create_warning_message(message: str) -> "DispatchedMessage":
        return DispatchedMessage(status=MessageLevel.WARNING, message=message)

    @staticmethod
    def create_info_message(message: str) -> "DispatchedMessage":
        return DispatchedMessage(status=MessageLevel.INFO, message=message)

    @staticmethod
    def create_debug_message(message: str) -> "DispatchedMessage":
        return DispatchedMessage(status=MessageLevel.DEBUG, message=message)

    def is_valid(self) -> bool:
        return self.message is not None
