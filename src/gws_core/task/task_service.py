

from .task_model import TaskModel


class TaskService():

    @classmethod
    def get_task_by_id(cls, id: str) -> TaskModel:
        return TaskModel.get_by_id_and_check(id=id)
