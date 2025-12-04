from gws_core.core.classes.search_builder import SearchBuilder
from gws_core.tag.tag_key_model import TagKeyModel


class TagSearchBuilder(SearchBuilder):
    def __init__(self) -> None:
        super().__init__(TagKeyModel, default_orders=[TagKeyModel.created_at.desc()])
