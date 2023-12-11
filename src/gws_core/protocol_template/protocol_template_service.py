# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.service.base_service import BaseService
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol_template.protocol_template_search_builder import \
    ProtocolTemplateSearchBuilder

from .protocol_template import ProtocolTemplate


class ProtocolTemplateService(BaseService):

    @classmethod
    def create_from_protocol(cls, protocol: ProtocolModel,
                             name: str, description: dict = None) -> ProtocolTemplate:

        protocol_template = ProtocolTemplate.from_protocol_model(protocol, name, description)
        return protocol_template.save()

    @classmethod
    def update(cls, id: str,
               protocol: ProtocolModel = None,
               name: str = None, description: dict = None) -> ProtocolTemplate:

        protocol_template = cls.get_by_id_and_check(id)

        if protocol:
            protocol_template.set_template(protocol.dumps_graph('config'))
        if name:
            protocol_template.name = name
        if description:
            protocol_template.description = description

        return protocol_template.save()

    @classmethod
    def get_by_id_and_check(cls, id: str) -> ProtocolTemplate:
        return ProtocolTemplate.get_by_id_and_check(id)

    @classmethod
    def delete(cls, id: str) -> None:
        ProtocolTemplate.delete_by_id(id)

    ############################## SEARCH ##############################

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[ProtocolTemplate]:

        search_builder: ProtocolTemplateSearchBuilder = ProtocolTemplateSearchBuilder()

        model_select = search_builder.add_search_params(search).build_search()
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_by_name(cls, name: str,
                       page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[ProtocolTemplate]:
        model_select = ProtocolTemplate.select().where(ProtocolTemplate.name.contains(name))

        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)
