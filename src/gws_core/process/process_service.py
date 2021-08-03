# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

from ..core.classes.paginator import Paginator
from ..core.dto.typed_tree_dto import TypedTree
from ..core.exception import NotFoundException
from ..core.model.model import Model
from ..core.model.typing import ProcessType
from ..core.service.base_service import BaseService
from ..experiment.experiment import Experiment
from ..progress_bar.progress_bar import ProgressBar
from .process import Process


class ProcessService(BaseService):

    # -- F --

    @classmethod
    def fetch_process(cls, type: str = "gws_core.process.process.Process", uri: str = "") -> Process:
        t = None
        if type:
            t = Model.get_model_type(type)
            if t is None:
                raise NotFoundException(
                    detail=f"Process type '{type}' not found")
        else:
            t = Process
        try:
            p = t.get(t.uri == uri)
            return p
        except Exception as err:
            raise NotFoundException(
                detail=f"No process found with uri '{uri}' and type '{type}'")

    @classmethod
    def fetch_process_progress_bar(cls, type_str: str = "gws_core.process.process.Process", uri: str = "") -> ProgressBar:
        try:
            return ProgressBar.get((ProgressBar.process_uri == uri) & (ProgressBar.process_type == type_str))
        except Exception as err:
            raise NotFoundException(
                detail=f"No progress bar found with process_uri '{uri}' and process_type '{type_str}'")

    @classmethod
    def fetch_process_list(cls,
                           type_str="gws_core.process.process.Process",
                           search_text: str = "",
                           experiment_uri: str = None,
                           page: int = 1,
                           number_of_items_per_page: int = 20,
                           as_json=False) -> Union[Paginator, List[Process], List[dict]]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        model_type = None
        if type_str:
            model_type = Model.get_model_type(type_str)
            if model_type is None:
                raise NotFoundException(
                    detail=f"Process type '{type_str}' not found")
        else:
            model_type = Process
        if search_text:
            query = model_type.search(search_text)
            result = []
            for o in query:
                if as_json:
                    result.append(o.get_related().to_json(shallow=True))
                else:
                    result.append(o.get_related())
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data': result,
                'paginator': paginator.paginator_dict()
            }
        else:
            if model_type is Process:
                #query = t.select(t.is_protocol == False).order_by(t.creation_datetime.desc())
                query = model_type.select().order_by(model_type.creation_datetime.desc())
            else:
                query = model_type.select().where(model_type.type == model_type.full_classname()
                                                  ).order_by(model_type.creation_datetime.desc())

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
            .where(ProcessType.root_model_type == "gws_core.process.process.Process")\
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
            .where(ProcessType.root_model_type == "gws_core.process.process.Process")\
            .order_by(ProcessType.model_type.asc())

        # create a fake main group to add processes in it
        tree: TypedTree = TypedTree('')

        for process_type in query:
            tree.add_object(
                process_type.get_model_types_array(), process_type.to_json())

        return tree.sub_trees
