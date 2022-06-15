# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Literal, Optional


class DispatchedMessage():
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
    def create_success_message(message: str) -> 'DispatchedMessage':
        return DispatchedMessage(status='SUCCESS', message=message)

    @staticmethod
    def create_progress_message(progress: float, message: str) -> 'DispatchedMessage':
        return DispatchedMessage(status='PROGRESS', message=message, progress=progress)

    @staticmethod
    def create_error_message(message: str) -> 'DispatchedMessage':
        return DispatchedMessage(status='ERROR', message=message)

    @staticmethod
    def create_warning_message(message: str) -> 'DispatchedMessage':
        return DispatchedMessage(status='WARNING', message=message)

    @staticmethod
    def create_info_message(message: str) -> 'DispatchedMessage':
        return DispatchedMessage(status='INFO', message=message)
