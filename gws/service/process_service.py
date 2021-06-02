# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Union

from gws.dto.process_type_dto import ProcessTypeTree
from gws.http import *
from gws.model import Experiment, Process, ProgressBar
from gws.query import Paginator
from gws.typing import ProcessType
from peewee import ModelSelect

from .base_service import BaseService


class ProcessService(BaseService):

    # -- F --

    @classmethod
    def fetch_process(cls, type: str = "gws.model.Process", uri: str = "") -> Process:

        from gws.service.model_service import ModelService
        t = None
        if type:
            t = ModelService.get_model_type(type)
            if t is None:
                raise HTTPNotFound(detail=f"Process type '{type}' not found")
        else:
            t = Process

        try:
            p = t.get(t.uri == uri)
            return p
        except Exception as err:
            raise HTTPNotFound(
                detail=f"No process found with uri '{uri}' and type '{type}'", debug_error=err)

    @classmethod
    def fetch_process_progress_bar(cls, type: str = "gws.model.Protocol", uri: str = "") -> ProgressBar:
        try:
            return ProgressBar.get((ProgressBar.process_uri == uri) & (ProgressBar.process_type == type))
        except Exception as err:
            raise HTTPNotFound(
                detail=f"No progress bar found with process_uri '{uri}' and process_type '{type}'", debug_error=err)

    @classmethod
    def fetch_process_list(cls,
                           type="gws.model.Process",
                           search_text: str = "",
                           experiment_uri: str = None,
                           page: int = 1,
                           number_of_items_per_page: int = 20,
                           as_json=False) -> Union[Paginator, List[Process], List[dict]]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        from gws.service.model_service import ModelService

        t = None
        if type:
            t = ModelService.get_model_type(type)
            if t is None:
                raise HTTPNotFound(detail=f"Process type '{type}' not found")
        else:
            t = Process

        if search_text:
            Q = t.search(search_text)
            result = []
            for o in Q:
                if as_json:
                    result.append(o.get_related().to_json(shallow=True))
                else:
                    result.append(o.get_related())

            P = Paginator(
                Q, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data': result,
                'paginator': P._paginator_dict()
            }
        else:
            if t is Process:
                Q = t.select().order_by(t.creation_datetime.desc())
            else:
                Q = t.select_me().order_by(t.creation_datetime.desc())

            if experiment_uri:
                Q = Q.join(Experiment, on=(t.experiment_id == Experiment.id))\
                    .where(Experiment.uri == experiment_uri)

            P = Paginator(
                Q, page=page, number_of_items_per_page=number_of_items_per_page)
            if as_json:
                return P.to_json(shallow=True)
            else:
                return P

    @classmethod
    def fetch_process_type_list(cls,
                                page: int = 1,
                                number_of_items_per_page: int = 20,
                                as_json=False) -> Union[Paginator, dict, List[ProcessType]]:

        query = ProcessType.select()\
            .where(ProcessType.base_ptype == "gws.model.Process")\
            .order_by(ProcessType.ptype.desc())

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json(shallow=True)
        else:
            return paginator

    @classmethod
    def fetch_process_type_grouped(cls) -> List[ProcessTypeTree]:
        """
        Return all the process types grouped by module and submodules
        """

        query: List[ProcessType] = ProcessType.select()\
            .where(ProcessType.base_ptype == "gws.model.Process")\
            .order_by(ProcessType.ptype.asc())

        # create a fake main group to add processes in it
        group: ProcessTypeTree = ProcessTypeTree('')

        for process_type in query:
            group.add_process_type(
                process_type.get_ptypes_array(), process_type.to_json())

        return group.sub_modules
