# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..process.process_interface import IProcess
from ..task.task_service import TaskService
from .task_model import TaskModel


class ITask(IProcess):

    _process_model: TaskModel

    def __init__(self, task_model: TaskModel) -> None:
        super().__init__(process_model=task_model)

    ############################################### CLASS METHODS ####################################

    @classmethod
    def get_by_id(cls, id: str) -> 'ITask':
        task_model: TaskModel = TaskService.get_task_by_id(id)
        return ITask(task_model)
