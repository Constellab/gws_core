

from fastapi import UploadFile

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.scenario_template.scenario_template_factory import \
    ScenarioTemplateFactory
from gws_core.scenario_template.scenario_template_search_builder import \
    ScenarioTemplateSearchBuilder

from .scenario_template import ScenarioTemplate


class ScenarioTemplateService():

    @classmethod
    def create_from_protocol(cls, protocol: ProtocolModel,
                             name: str, description: dict = None) -> ScenarioTemplate:

        scenario_template = ScenarioTemplateFactory.from_protocol_model(protocol, name, description)
        return scenario_template.save()

    @classmethod
    def create_from_file(cls, file: UploadFile) -> ScenarioTemplate:
        scenario_template = ScenarioTemplateFactory.from_export_dto_str(file.file.read().decode('utf-8'))
        return scenario_template.save()

    @classmethod
    def update(cls, id: str,
               protocol: ProtocolModel = None,
               name: str = None, description: dict = None) -> ScenarioTemplate:

        scenario_template = cls.get_by_id_and_check(id)

        if protocol:
            scenario_template.set_template(protocol.to_protocol_config_dto())
        if name:
            scenario_template.name = name
        if description:
            scenario_template.description = description

        return scenario_template.save()

    @classmethod
    def update_name(cls, id: str, name: str) -> ScenarioTemplate:
        scenario_template = cls.get_by_id_and_check(id)
        scenario_template.name = name
        return scenario_template.save()

    @classmethod
    def get_by_id_and_check(cls, id: str) -> ScenarioTemplate:
        return ScenarioTemplate.get_by_id_and_check(id)

    @classmethod
    def delete(cls, id: str) -> None:
        ScenarioTemplate.delete_by_id(id)

    ############################## SEARCH ##############################

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[ScenarioTemplate]:

        search_builder: ScenarioTemplateSearchBuilder = ScenarioTemplateSearchBuilder()

        model_select = search_builder.add_search_params(search).build_search()
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_by_name(cls, name: str,
                       page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[ScenarioTemplate]:
        model_select = ScenarioTemplate.select().where(ScenarioTemplate.name.contains(name))

        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)
