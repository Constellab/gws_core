

from fastapi import UploadFile

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.scenario_component.scenario_component_factory import \
    ScenarioComponentFactory
from gws_core.scenario_component.scenario_component_search_builder import \
    ScenarioComponentSearchBuilder

from .scenario_component import ScenarioComponent


class ScenarioComponentService():

    @classmethod
    def create_from_protocol(cls, protocol: ProtocolModel,
                             name: str, description: dict = None) -> ScenarioComponent:

        scenario_component = ScenarioComponentFactory.from_protocol_model(protocol, name, description)
        return scenario_component.save()

    @classmethod
    def create_from_file(cls, file: UploadFile) -> ScenarioComponent:
        scenario_component = ScenarioComponentFactory.from_export_dto_str(file.file.read().decode('utf-8'))
        return scenario_component.save()

    @classmethod
    def update(cls, id: str,
               protocol: ProtocolModel = None,
               name: str = None, description: dict = None) -> ScenarioComponent:

        scenario_component = cls.get_by_id_and_check(id)

        if protocol:
            scenario_component.set_graph(protocol.to_protocol_config_dto())
        if name:
            scenario_component.name = name
        if description:
            scenario_component.description = description

        return scenario_component.save()

    @classmethod
    def update_name(cls, id: str, name: str) -> ScenarioComponent:
        scenario_component = cls.get_by_id_and_check(id)
        scenario_component.name = name
        return scenario_component.save()

    @classmethod
    def get_by_id_and_check(cls, id: str) -> ScenarioComponent:
        return ScenarioComponent.get_by_id_and_check(id)

    @classmethod
    def delete(cls, id: str) -> None:
        ScenarioComponent.delete_by_id(id)

    ############################## SEARCH ##############################

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[ScenarioComponent]:

        search_builder: ScenarioComponentSearchBuilder = ScenarioComponentSearchBuilder()

        model_select = search_builder.add_search_params(search).build_search()
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_by_name(cls, name: str,
                       page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[ScenarioComponent]:
        model_select = ScenarioComponent.select().where(ScenarioComponent.name.contains(name))

        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)
