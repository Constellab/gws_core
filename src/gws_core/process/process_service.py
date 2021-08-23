# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type, Union

from ..core.classes.paginator import Paginator
from ..core.dto.typed_tree_dto import TypedTree
from ..core.exception.exceptions import NotFoundException
from ..core.service.base_service import BaseService
from ..experiment.experiment import Experiment
from ..process.processable_factory import ProcessableFactory
from ..progress_bar.progress_bar import ProgressBar
from .process import Process
from .process_model import ProcessModel
from .process_type import ProcessType


class ProcessService(BaseService):

    # -- F --

    @classmethod
    def get_process_by_uri(cls, uri: str) -> ProcessModel:
        return ProcessModel.get_by_uri(uri=uri)

    @classmethod
    def fetch_process_progress_bar(cls, uri: str) -> ProgressBar:
        try:
            return ProgressBar.get_by_process_uri(uri)
        except Exception:
            raise NotFoundException(
                detail=f"No progress bar found with process_uri '{uri}'")

    @classmethod
    def fetch_process_list(cls,
                           experiment_uri: str = None,
                           page: int = 1,
                           number_of_items_per_page: int = 20,
                           as_json=False) -> Union[Paginator, List[ProcessModel], List[dict]]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        query = ProcessModel.select().order_by(ProcessModel.creation_datetime.desc())

        if experiment_uri:
            query = query.join(Experiment, on=(ProcessModel.experiment_id == Experiment.id))\
                .where(Experiment.uri == experiment_uri)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json()
        else:
            return paginator

    @classmethod
    def fetch_process_type_list(cls,
                                page: int = 1,
                                number_of_items_per_page: int = 20,
                                as_json=False) -> Union[Paginator, dict]:

        query = ProcessType.get_types()

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json()
        else:
            return paginator

    @classmethod
    def fetch_process_type_tree(cls) -> List[TypedTree]:
        """
        Return all the process types grouped by module and submodules
        """

        query: List[ProcessType] = ProcessType.get_types()

        # create a fake main group to add processes in it
        tree: TypedTree = TypedTree('')

        for process_type in query:
            tree.add_object(
                process_type.get_model_types_array(), process_type.to_json())

        return tree.sub_trees

    @classmethod
    def create_process_from_type(cls, process_type: Type[Process], instance_name: str = None) -> ProcessModel:
        process: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=process_type, instance_name=instance_name)

        process.save_full()

        return process
