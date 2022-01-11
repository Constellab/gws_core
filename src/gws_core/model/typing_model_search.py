
from gws_core.model.typing import Typing

from ..core.classes.search_builder import SearchBuilder, SearchFilterCriteria


class TypingModelSearchBuilder(SearchBuilder):

    def __init__(self) -> None:
        super().__init__(Typing, default_order=[Typing.human_name.asc()])
