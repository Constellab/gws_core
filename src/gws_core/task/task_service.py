# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..core.service.base_service import BaseService
from .task_model import TaskModel


class TaskService(BaseService):

    @classmethod
    def get_task_by_id(cls, id: str) -> TaskModel:
        return TaskModel.get_by_id_and_check(id=id)
