# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.tag.entity_tag import EntityTagType
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder

from .view_config import ViewConfig


class ViewConfigSearchBuilder(EntityWithTagSearchBuilder):
    """Search build for the view cofnig

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(ViewConfig, EntityTagType.VIEW,
                         default_orders=[ViewConfig.last_modified_at.desc()])
