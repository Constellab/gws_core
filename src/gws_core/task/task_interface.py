# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..process.process_interface import IProcess
from .task_model import TaskModel

if TYPE_CHECKING:
    from ..protocol.protocol_interface import IProtocol


class ITask(IProcess):

    _task_model: TaskModel

    def __init__(self, task_model: TaskModel, parent_protocol: Optional[IProtocol]) -> None:
        super().__init__(process_model=task_model, parent_protocol=parent_protocol)
        self._task_modell = task_model
