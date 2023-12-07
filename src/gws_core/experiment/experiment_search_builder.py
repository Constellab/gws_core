# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Type

from peewee import Expression

from gws_core.core.classes.search_builder import SearchFilterCriteria
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.model.typing_name import TypingNameObj
from gws_core.process.process_model import ProcessModel
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder

from .experiment import Experiment


class ExperimentSearchBuilder(EntityWithTagSearchBuilder):

    def __init__(self) -> None:
        super().__init__(Experiment, EntityType.EXPERIMENT,
                         default_orders=[Experiment.last_modified_at.desc()])

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        if filter_['key'] == 'process_typing_name':

            typing_name = TypingNameObj.from_typing_name(filter_['value'])

            entity_alias: Type[ProcessModel] = typing_name.get_model_type().alias()

            self.add_join(entity_alias, on=((entity_alias.experiment == self._model_type.id) &
                                            (entity_alias.process_typing_name == filter_['value'])
                                            ))

            return None

        return super().convert_filter_to_expression(filter_)
