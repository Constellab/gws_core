# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type

from gws_core.config.config_types import ConfigParamsDict
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.resource import Resource

from ..core.classes.paginator import Paginator
from ..core.dto.typed_tree_dto import TypedTree
from ..core.service.base_service import BaseService
from ..process.process_factory import ProcessFactory
from .task import Task
from .task_model import TaskModel
from .task_typing import TaskTyping


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

        ############################# TASK TYPE ###########################

    @classmethod
    def get_task_typing(cls, id: str) -> TaskTyping:
        return TaskTyping.get_by_id_and_check(id)

    @classmethod
    def get_task_typing_list(cls,
                             page: int = 0,
                             number_of_items_per_page: int = 20) -> Paginator[TaskTyping]:

        query = TaskTyping.get_types()

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_task_typing_tree(cls) -> List[TypedTree]:
        """
        Return all the task types grouped by module and submodules
        """

        query: List[TaskTyping] = TaskTyping.get_types()

        # create a fake main group to add taskes in it
        tree: TypedTree = TypedTree('')

        for task_type in query:
            tree.add_object(
                task_type.get_model_types_array(), task_type.to_json())

        return tree.sub_trees

    @classmethod
    def get_task_typing_by_related_resource(cls, related_resource_typing_name: str) -> List[TaskTyping]:
        resource_type: Type[Resource] = TypingManager.get_type_from_name(related_resource_typing_name)

        return TaskTyping.get_by_related_resource(resource_type)
