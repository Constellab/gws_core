from ..process.process_proxy import ProcessProxy
from .task_model import TaskModel
from .task_service import TaskService


class TaskProxy(ProcessProxy):
    _process_model: TaskModel

    def __init__(self, task_model: TaskModel) -> None:
        super().__init__(process_model=task_model)

    ############################################### CLASS METHODS ####################################

    @classmethod
    def get_by_id(cls, id_: str) -> "TaskProxy":
        task_model: TaskModel = TaskService.get_task_by_id(id_)
        return TaskProxy(task_model)
