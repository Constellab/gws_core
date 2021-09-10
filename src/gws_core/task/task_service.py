# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type

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
    def get_task_by_uri(cls, uri: str) -> TaskModel:
        return TaskModel.get_by_uri(uri=uri)

    @classmethod
    def fetch_task_list(cls,
                        page: int = 0,
                        number_of_items_per_page: int = 20) -> Paginator[TaskModel]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        query = TaskModel.select().order_by(TaskModel.creation_datetime.desc())
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def create_task_model_from_type(cls, task_type: Type[Task], instance_name: str = None) -> TaskModel:
        task: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=task_type, instance_name=instance_name)

        task.save_full()

        return task

        ############################# TASK TYPE ###########################

    @classmethod
    def get_task_typing(cls, uri: str) -> TaskTyping:
        return TaskTyping.get_by_uri_and_check(uri)

    @classmethod
    def fetch_task_typing_list(cls,
                               page: int = 0,
                               number_of_items_per_page: int = 20) -> Paginator[TaskTyping]:

        query = TaskTyping.get_types()

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def fetch_task_typing_tree(cls) -> List[TypedTree]:
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
