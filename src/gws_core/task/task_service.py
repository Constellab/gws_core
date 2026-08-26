from .task_model import TaskModel


class TaskService:
    @classmethod
    def get_task_by_id(cls, id_: str) -> TaskModel:
        return TaskModel.get_by_id_and_check(id_=id_)
