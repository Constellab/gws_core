# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type, Union

from gws_core.model.typing_manager import TypingManager

from ..core.classes.paginator import Paginator
from ..core.dto.typed_tree_dto import TypedTree
from ..core.exception.exceptions import NotFoundException
from ..core.service.base_service import BaseService
from ..experiment.experiment import Experiment
from ..progress_bar.progress_bar import ProgressBar
from .process import CONST_PROCESS_TYPING_NAME, Process
from .process_type import ProcessType


class ProcessService(BaseService):

    # -- F --

    @classmethod
    def fetch_process(cls, typing_name: str = CONST_PROCESS_TYPING_NAME, uri: str = "") -> Process:
        return TypingManager.get_object_with_typing_name_and_uri(typing_name, uri)

    @classmethod
    def fetch_process_progress_bar(cls, process_typing_name: str = CONST_PROCESS_TYPING_NAME, uri: str = "") -> ProgressBar:
        try:
            return ProgressBar.get_by_process_typing_name_and_process_uri(process_typing_name, uri)
        except Exception:
            raise NotFoundException(
                detail=f"No progress bar found with process_uri '{uri}' and process_type '{process_typing_name}'")

    @classmethod
    def fetch_process_list(cls,
                           typing_name=CONST_PROCESS_TYPING_NAME,
                           experiment_uri: str = None,
                           page: int = 1,
                           number_of_items_per_page: int = 20,
                           as_json=False) -> Union[Paginator, List[Process], List[dict]]:
        model_type: Type[Process] = TypingManager.get_type_from_name(
            typing_name)

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        if model_type is Process:
            query = model_type.select_me().order_by(model_type.creation_datetime.desc())
        else:
            query = model_type.select_me().order_by(model_type.creation_datetime.desc())

        if experiment_uri:
            query = query.join(Experiment, on=(model_type.experiment_id == Experiment.id))\
                .where(Experiment.uri == experiment_uri)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json(shallow=True)
        else:
            return paginator

    @classmethod
    def fetch_process_type_list(cls,
                                page: int = 1,
                                number_of_items_per_page: int = 20,
                                as_json=False) -> Union[Paginator, dict]:

        query = ProcessType.select()\
            .where(ProcessType.object_type == "PROCESS")\
            .order_by(ProcessType.model_type.desc())

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json(shallow=True)
        else:
            return paginator

    @classmethod
    def fetch_process_type_tree(cls) -> List[TypedTree]:
        """
        Return all the process types grouped by module and submodules
        """

        query: List[ProcessType] = ProcessType.select()\
            .where(ProcessType.object_type == "PROCESS")\
            .order_by(ProcessType.model_type.asc())

        # create a fake main group to add processes in it
        tree: TypedTree = TypedTree('')

        for process_type in query:
            tree.add_object(
                process_type.get_model_types_array(), process_type.to_json())

        return tree.sub_trees
