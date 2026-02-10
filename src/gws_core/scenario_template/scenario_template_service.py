from fastapi import UploadFile

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.scenario_template.scenario_template_factory import ScenarioTemplateFactory
from gws_core.scenario_template.scenario_template_search_builder import (
    ScenarioTemplateSearchBuilder,
)
from gws_core.tag.tag import Tag
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.tag_service import TagService

from .scenario_template import ScenarioTemplate


class ScenarioTemplateService:
    @classmethod
    def create_from_protocol(
        cls, protocol: ProtocolModel, name: str, description: RichTextDTO | None = None
    ) -> ScenarioTemplate:
        scenario_template = ScenarioTemplateFactory.from_protocol_model(protocol, name, description)
        return scenario_template.save()

    @classmethod
    def create_from_file(cls, file: UploadFile) -> ScenarioTemplate:
        scenario_template = ScenarioTemplateFactory.from_export_dto_str(
            file.file.read().decode("utf-8")
        )
        return scenario_template.save()

    @classmethod
    def update(
        cls,
        id_: str,
        protocol: ProtocolModel | None = None,
        name: str | None = None,
        description: RichTextDTO | None = None,
    ) -> ScenarioTemplate:
        scenario_template = cls.get_by_id_and_check(id_)

        if protocol:
            scenario_template.set_template(protocol.to_protocol_config_dto())
        if name:
            scenario_template.name = name
        if description:
            scenario_template.description = description

        return scenario_template.save()

    @classmethod
    def update_name(cls, id_: str, name: str | None = None) -> ScenarioTemplate:
        scenario_template = cls.get_by_id_and_check(id_)
        if name:
            scenario_template.name = name
        return scenario_template.save()

    @classmethod
    def get_by_id_and_check(cls, id_: str) -> ScenarioTemplate:
        return ScenarioTemplate.get_by_id_and_check(id_)

    @classmethod
    def get_by_tag(cls, tag_key: str, tag_value: str) -> ScenarioTemplate:
        """Get a scenario template by tag

        :param tag_key: The tag key to search for
        :param tag_value: The tag value to search for
        :return: The scenario template
        :raises BadRequestException: If no template is found or multiple templates are found
        """
        tag = Tag(key=tag_key, value=tag_value)
        templates = TagService.get_entities_by_tag(TagEntityType.SCENARIO_TEMPLATE, tag)

        if len(templates) == 0:
            raise BadRequestException(f"No scenario template found with tag {tag_key}={tag_value}")
        if len(templates) > 1:
            raise BadRequestException(
                f"Multiple scenario templates found with tag {tag_key}={tag_value}"
            )

        return templates[0]

    @classmethod
    def delete(cls, id_: str) -> None:
        ScenarioTemplate.delete_by_id(id_)

    ############################## SEARCH ##############################

    @classmethod
    def search(
        cls, search: SearchParams, page: int = 0, number_of_items_per_page: int = 20
    ) -> Paginator[ScenarioTemplate]:
        search_builder: ScenarioTemplateSearchBuilder = ScenarioTemplateSearchBuilder()

        return search_builder.add_search_params(search).search_page(page, number_of_items_per_page)

    @classmethod
    def search_by_name(
        cls, name: str, page: int = 0, number_of_items_per_page: int = 20
    ) -> Paginator[ScenarioTemplate]:
        model_select = ScenarioTemplate.select().where(ScenarioTemplate.name.contains(name))

        return Paginator(model_select, page=page, nb_of_items_per_page=number_of_items_per_page)
