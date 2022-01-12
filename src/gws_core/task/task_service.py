# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core.config.config_types import ConfigParamsDict

from ..core.service.base_service import BaseService
from ..process.process_factory import ProcessFactory
from .task import Task
from .task_model import TaskModel


class TaskService(BaseService):

    # -- F --

    @classmethod
    def get_task_by_id(cls, id: str) -> TaskModel:
        return TaskModel.get_by_id_and_check(id=id)

    @classmethod
    def create_task_model_from_type(cls, task_type: Type[Task], instance_name: str = None,
                                    config_params: ConfigParamsDict = None) -> TaskModel:
        task: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=task_type, instance_name=instance_name, config_params=config_params)

        task.save_full()

        return task
