# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict, List

from peewee import ModelSelect

from ...core.classes.paginator import Paginator
from ...core.classes.search_builder import SearchBuilder, SearchParams
from ...task.transformer.transformer_type import TransformerDict
from ..resource_model import ResourceModel
from ..view import View
from .view_historic import ViewHistoric
from .view_historic_search_builder import ViewHistoricSearchBuilder


class ViewHistoricService():

    MAX_HISTORY_SIZE = 100

    @classmethod
    def save_resource_view_historic(cls, resource_model: ResourceModel, view: View,
                                    view_name: str, config_values: Dict[str, Any],
                                    transformers: List[TransformerDict] = None) -> None:
        historic_view: ViewHistoric = ViewHistoric(
            resource_model=resource_model,
            experiment=resource_model.experiment,
            title=view.get_title(),
            caption=view.get_caption(),
            view_name=view_name,
            view_type=view.get_type(),
            config_values=config_values,
            transformers=transformers,
        )

        historic_view.save()

        # limite the length of the history
        if(ViewHistoric.select().count() > cls.MAX_HISTORY_SIZE):
            view_historic: ViewHistoric = ViewHistoric.select().order_by(ViewHistoric.created_at.asc()).first()
            view_historic.delete_instance()

    @classmethod
    def search(cls, search: SearchParams,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:

        search_builder: SearchBuilder = ViewHistoricSearchBuilder()

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)
