from typing import Type

from peewee import Expression

from gws_core.core.classes.search_builder import SearchFilterCriteria
from gws_core.model.typing_name import TypingNameObj
from gws_core.process.process_model import ProcessModel
from gws_core.tag.entity_with_tag_search_builder import EntityWithTagSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType

from .scenario import Scenario
from .scenario_enums import ScenarioStatus


class ScenarioSearchBuilder(EntityWithTagSearchBuilder):
    def __init__(self) -> None:
        super().__init__(
            Scenario, TagEntityType.SCENARIO, default_orders=[Scenario.last_modified_at.desc()]
        )

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        if filter_.key == "process_typing_name":
            self.add_contains_process_filter(filter_.value)

            return None

        return super().convert_filter_to_expression(filter_)

    def add_title_filter(self, title: str) -> "ScenarioSearchBuilder":
        """Filter the search query where title contains the name"""
        self.add_expression(Scenario.title.contains(title))
        return self

    def add_status_filter(self, status: ScenarioStatus) -> "ScenarioSearchBuilder":
        """Filter the search query by a specific status"""
        self.add_expression(Scenario.status == status)
        return self

    def add_folder_filter(self, folder_id: str) -> "ScenarioSearchBuilder":
        """Filter the search query by a specific folder"""
        self.add_expression(Scenario.folder == folder_id)
        return self

    def add_contains_process_filter(self, process_typing_name: str) -> "ScenarioSearchBuilder":
        """Filter the search query to scenarios that contains a specific process"""
        typing_name = TypingNameObj.from_typing_name(process_typing_name)

        entity_alias: Type[ProcessModel] = typing_name.get_model_type().alias()

        self.add_join(
            entity_alias,
            on=(
                (entity_alias.scenario == self._model_type.id)
                & (entity_alias.process_typing_name == process_typing_name)
            ),
        )
        return self

    def add_is_archived_filter(self, is_archived: bool) -> "ScenarioSearchBuilder":
        """Filter the search query by a specific archived status"""
        self.add_expression(Scenario.is_archived == is_archived)
        return self
