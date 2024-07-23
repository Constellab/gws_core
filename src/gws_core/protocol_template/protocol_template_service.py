

from fastapi import UploadFile

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol_template.protocol_template_factory import \
    ProtocolTemplateFactory
from gws_core.protocol_template.protocol_template_search_builder import \
    ProtocolTemplateSearchBuilder

from .protocol_template import ProtocolTemplate


class ProtocolTemplateService():

    @classmethod
    def create_from_protocol(cls, protocol: ProtocolModel,
                             name: str, description: dict = None) -> ProtocolTemplate:

        protocol_template = ProtocolTemplateFactory.from_protocol_model(protocol, name, description)
        return protocol_template.save()

    @classmethod
    def create_from_file(cls, file: UploadFile) -> ProtocolTemplate:
        protocol_template = ProtocolTemplateFactory.from_export_dto_str(file.file.read().decode('utf-8'))
        return protocol_template.save()

    @classmethod
    def update(cls, id: str,
               protocol: ProtocolModel = None,
               name: str = None, description: dict = None) -> ProtocolTemplate:

        protocol_template = cls.get_by_id_and_check(id)

        if protocol:
            protocol_template.set_template(protocol.to_protocol_config_dto())
        if name:
            protocol_template.name = name
        if description:
            protocol_template.description = description

        return protocol_template.save()

    @classmethod
    def update_name(cls, id: str, name: str) -> ProtocolTemplate:
        protocol_template = cls.get_by_id_and_check(id)
        protocol_template.name = name
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
