# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder

from .experiment import Experiment


class ExperimentSearchBuilder(EntityWithTagSearchBuilder):

    def __init__(self) -> None:
        super().__init__(Experiment, EntityType.EXPERIMENT,
                         default_orders=[Experiment.last_modified_at.desc()])
