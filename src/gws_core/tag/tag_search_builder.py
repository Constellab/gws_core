
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder
from gws_core.tag.tag_key_model import TagKeyModel


class TagSearchBuilder(EntityWithTagSearchBuilder):
    def __init__(self) -> None:
        super().__init__(TagKeyModel, None,
                         default_orders=[TagKeyModel.created_at.desc()])
